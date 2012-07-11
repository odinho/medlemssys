#!/usr/bin/env python
# vim: set fileencoding=UTF8 tabstop=4 softtabstop=4 expandtab autoindent :

import datetime
import sys

import mod10

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

def parse_ocr(ocrfile):
    for row in ocrfile:
        row = row.strip()
        if row[0:8] == "NY000010":
            # Startrecord for sending
            forsendelsesnr = row[16:23]
            break

    if not forsendelsesnr:
        raise Exception('Fann ikkje startrecord for sending')

    info = []

    for row in ocrfile:
        row = row.strip()

        if row[0:6] == "NY0900":
            if row[6:8] == "20":
                # Startrecord for oppdrag
                pass
            elif row[6:8] == "88":
                # Sluttrecord for oppdrag
                pass
            else:
                raise Exception("Forstår ikkje kode {0} ({1})!".format(row[6:8], row))
            continue

        elif row[0:4] == "NY09":
            if row[6:8] != "30":
                raise Exception("Venta startrecord 30, fekk {0}. ({1})!".format(row[6:8], row))

            # Transaksjon
            trans = TRANSAKSJONSTYPE[row[4:6]]
            dato = row[15:21]
            dato = datetime.date(2000 + int(dato[4:6]), int(dato[2:4]), int(dato[0:2]))
            belop = int(row[32:49])/100.0
            kid = row[49:74].strip()
            if not mod10.check_number(kid.strip()):
                raise Exception("KID-nummer validerte ikkje ({0})".format(kid))

            row2 = ocrfile.next()
            oppdr_dato = row2[41:47]
            fra_konto = row2[47:58]

            fritekst = ""
            if row[4:6] == "20" or row[4:6] == "21":
                row3 = ocrfile.next()
                fritekst = row3[15:55]

            info.append(dict(
                        transaksjon=trans,
                        dato=dato,
                        belop=belop,
                        kid=kid,
                        oppdragsdato=oppdr_dato,
                        fra_konto=fra_konto,
                        fritekst=fritekst,
                    ))
    return info

if __name__ == '__main__':
    if (len(sys.argv) < 2):
        print "Usage:  %s <in_ocr_file>\n" % sys.argv[0]
        sys.exit()

    info = parse_ocr(open(sys.argv[1]))

    for f in info:
        print "{dato} {belop:6} {transaksjon:30} {kid}".format(**f)
