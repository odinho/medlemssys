# -*- coding: utf-8 -*-
# vim: shiftwidth=4 tabstop=4 expandtab softtabstop=4 ai

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
from __future__ import print_function

import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.db import transaction
from django.db.models import Q

from medlemssys.medlem.models import Giro
from medlemssys.medlem.models import update_denormalized_fields
from medlemssys.ocr import parse_ocr

obj = ""

class Command(BaseCommand):
    args = '[ ocr_fil.txt ]'
    help = 'Registrerer OCR-innbetalingar'

    @transaction.atomic
    def handle(self, *args, **options):
        if len(args):
            fn = args[0]
        else:
            fn = getattr(settings, 'OCR_FIL', 'ocr.txt')

        if not os.path.isfile(fn):
            raise CommandError("Fila finst ikkje ({0})".format(fn).encode('utf8'))

        ocr_file = open(fn)
        ocr = parse_ocr(ocr_file)

        for f in ocr:
            try:
                giro = Giro.objects.get(
                        Q(oppretta__year=f['dato'].year) | Q(oppretta__year=(f['dato'].year - 1)),
                        kid=f['kid'],
                    )
            except Giro.DoesNotExist:
                self.err("Fann ikkje giroen, {dato:6s} {belop:4n} {kid:12s} {transaksjon}".format(**f))
                continue

            if f['belop'] < giro.belop:
                self.err("{giro}: for lite betalt! Rekna {giro.belop}, fekk {belop} ({giro.pk})".format(giro=giro, belop=f['belop']))
            elif f['belop'] > giro.belop:
                # XXX: Splitt opp? Registrer ein donasjon?
                self.err("{giro}: Betalte meir, venta {giro.belop}, fekk {belop} ({giro.pk})".format(giro=giro, belop=f['belop']))
                giro.innbetalt = f['dato']
            else:
                giro.innbetalt = f['dato']
                #self.err("{belop:3n}kr ({giro.pk}) {giro} ".format(giro=giro, belop=f['belop']))

            giro.innbetalt_belop = f['belop']
            giro.status = 'F'
            if giro.desc:
                giro.desc += '\nOCR'
            else:
                giro.desc = 'OCR'
            giro.save()
            self.err(u"{giro}: Betalte {giro.belop} ({giro.pk})".format(giro=giro))

            if giro.medlem.status == 'I' and giro.innbetalt_belop >= giro.belop:
                self.err("{medlem} var infoperson, flyttar til medlem etter betaling".format(medlem=giro.medlem))
                giro.medlem.status = 'M'
                giro.medlem.save()

        update_denormalized_fields()


    def err(self, msg):
        self.stderr.write((unicode(msg) + "\n").encode('utf-8'))
