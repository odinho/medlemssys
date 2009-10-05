#!/usr/bin/env python
# vim: set fileencoding=UTF8 tabstop=4 softtabstop=4 expandtab autoindent :

import sys, mod10

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

if (len(sys.argv) < 2):
    print "Usage:  %s <in_ocr_file>\n" % sys.argv[0]
    sys.exit()

ocrfile = open(sys.argv[1])

for row in ocrfile:
    row = row.strip()
    if row[0:8] == "NY000010":
        print "# Startrecord for forsendelse"
        forsendelsesnr = row[16:23]
        break

if not forsendelsesnr:
    print "# Fann ikkje startrecord for forsendelse"
    sys.exit()

for row in ocrfile:
    row = row.strip()

    if row[0:6] == "NY0900":
        if row[6:8] == "20":
            print "# Startrecord for oppdrag"
            print "%7s [%6s] %6s  %s" % ("dato", "kid", "belop", "transaksjon")
        elif row[6:8] == "88":
            print "# Sluttrecord for oppdrag"
        else:
            print "# Forstår ikkje kode!"
        continue

    elif row[0:4] == "NY09":
        if row[6:8] != "30":
            print "# Venta startrecord, dette er ikkje!"
            print row
            sys.exit()

        # Transaksjon
        trans = TRANSAKSJONSTYPE[row[4:6]]
        dato = row[15:21]
        belop = int(row[32:49])/100.0
        kid = row[49:74]
        if mod10.check_number(kid.strip()):
            kid_ok = "KID ok"
        else:
            kid_ok = "KID FEIL"

        row2 = ocrfile.next()
        oppdr_dato = row2[41:47]
        fra_konto = row2[47:58]

        print "%7s [%6s] %6d  %s" % (dato, kid_ok, belop, trans)

        if row[4:6] == "20" or row[4:6] == "21":
            row3 = ocrfile.next()
            fritekst = row3[15:55]
            print fritekst
