# -*- coding: utf-8 -*-
# vim: ts=4 sts=4 expandtab ai

# Copyright 2009-2014 Odin Hørthe Omdal

# This file is part of Medlemssys.

# Medlemssys is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Medlemssys is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with Medlemssys.  If not, see <http://www.gnu.org/licenses/>.
import datetime
import logging
from django.db.models import Q

from medlemssys.medlem.models import Giro
from medlemssys.medlem.models import update_denormalized_fields

from . import mod10

logger = logging.getLogger(__name__)

class OCRError(Exception):
    pass


class OCR(object):
    TRANSAKSJONSTYPE = {
        "10": "Giro belasta konto",
        "11": "Faste oppdrag",
        "12": "Direkte remittering",
        "13": "Bedriftsterminalgiro (BTG)",
        "14": "Skrankegiro",
        "15": "AvtaleGiro",
        "16": "TeleGiro",
        "17": "Giro - betalt kontant",
        "18": "Nettgiro - reversering m KID",
        "19": "Nettgiro - kjøp m KID",
        "20": "Nettgiro - reversering m fritekst",
        "21": "Nettgiro - kjøp m fritekst",
    }

    def __init__(self):
        self.data = []

    def from_filename(self, path):
        fp = open(path)
        self._parse(fp)

    def from_string(self, string):
        self._parse(iter(string.splitlines()))

    def process_to_db(self):
        for f in self.data:
            f['msg'] = []
            f['giro'] = None
            f['processed'] = False
            try:
                giro = Giro.objects.get(
                        Q(oppretta__year=f['dato'].year) | Q(oppretta__year=(f['dato'].year - 1)),
                        kid=f['kid'])
            except Giro.DoesNotExist:
                msg = "Fann ikkje giroen, {dato:6s} {belop:4n} {kid:12s} {transaksjon}".format(**f)
                logger.warning(msg)
                f['msg'].append(msg)
                continue
            f['giro'] = giro
            if giro.betalt():
                msg = "Giroen ({0}) er allereie betalt".format(giro.admin_change())
                f['msg'].append(msg)
                logger.warning("{giro.medlem}: {msg}".format(giro=giro, msg=msg))
                continue

            if f['belop'] < giro.belop:
                msg = "{giro}: for lite betalt! Rekna {giro.belop}, fekk {belop} ({giro.pk})".format(giro=giro, belop=f['belop'])
                logger.warning("{giro.medlem}: {msg}".format(giro=giro, msg=msg))
                f['msg'].append(msg)
            elif f['belop'] > giro.belop:
                # XXX: Splitt opp? Registrer ein donasjon?
                msg = "{giro}: Betalte meir, venta {giro.belop}, fekk {belop} ({giro.pk})".format(giro=giro, belop=f['belop'])
                logger.info("{giro.medlem}: {msg}".format(giro=giro, msg=msg))
                f['msg'].append(msg)
                giro.innbetalt = f['dato']
            else:
                giro.innbetalt = f['dato']
                #self.err("{belop:3n}kr ({giro.pk}) {giro} ".format(giro=giro, belop=f['belop']))

            giro.innbetalt_belop = f['belop']
            giro.konto = 'A' # Medlemskonto (KID)
            if giro.desc:
                giro.desc += '\nOCR'
            else:
                giro.desc = 'OCR'
            giro.save()
            f['processed'] = True

            if giro.medlem.status == 'I' and giro.innbetalt_belop >= giro.belop:
                f['msg'].append("{medlem} var infoperson, flyttar til medlem etter betaling".format(medlem=giro.medlem))
                giro.medlem.status = 'M'
                giro.medlem.save()

        update_denormalized_fields()


    def _parse(self, ocr_data):
        for row in ocr_data:
            row = row.strip()
            if row[0:8] == "NY000010":
                # Startrecord for sending
                #forsendelsesnr = row[16:23]
                break
        else:
            raise OCRError('Fann ikkje startrecord for sending')

        for row in ocr_data:
            row = row.strip()

            if row[0:6] == "NY0900":
                if row[6:8] == "20":
                    # Startrecord for oppdrag
                    pass
                elif row[6:8] == "88":
                    # Sluttrecord for oppdrag
                    pass
                else:
                    raise OCRError("Forstår ikkje kode {0} ({1})!".format(row[6:8], row))
                continue

            elif row[0:4] == "NY09":
                if row[6:8] != "30":
                    raise OCRError("Venta startrecord 30, fekk {0}. ({1})!".format(row[6:8], row))

                # Transaksjon
                trans = self.TRANSAKSJONSTYPE[row[4:6]]
                dato = row[15:21]
                dato = datetime.date(2000 + int(dato[4:6]), int(dato[2:4]), int(dato[0:2]))
                belop = int(row[32:49])/100.0
                kid = row[49:74].strip()
                if not mod10.check_number(kid.strip()):
                    raise OCRError("KID-nummer validerte ikkje ({0})".format(kid))

                row2 = ocr_data.next()
                oppdr_dato = row2[41:47]
                fra_konto = row2[47:58]

                fritekst = ""
                if row[4:6] == "20" or row[4:6] == "21":
                    row3 = ocr_data.next()
                    fritekst = row3[15:55]

                self.data.append(dict(
                            transaksjon=trans,
                            dato=dato,
                            belop=belop,
                            kid=kid,
                            oppdragsdato=oppdr_dato,
                            fra_konto=fra_konto,
                            fritekst=fritekst,
                        ))
        return self.data
