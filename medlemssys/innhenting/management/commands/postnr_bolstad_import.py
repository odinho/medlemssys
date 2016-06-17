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

import csv
import os

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from medlemssys.medlem.models import PostNummer

obj = ""

class Command(BaseCommand):
    args = '<Tab seperated Erik Bolstad postnr-CSV files>'
    help = """Importerer medlemane inn i databasen"""

    def handle(self, *args, **options):
        global obj
        obj = self
        if 'force_update' in options:
            self.force_update = True

        if not os.path.isfile(args[0]):
            raise CommandError("Fila finst ikkje ({0})".format(args[0]).encode('utf8'))

        # 0       1         2                3            4         5      6       7        8      9    10   11            12                       13
        # POSTNR, POSTSTAD, POSTNR- OG STAD, BRUKSOMRÅDE, FOLKETAL, BYDEL, KOMMNR, KOMMUNE, FYLKE, LAT, LON, DATAKVALITET, DATAKVALITETSFORKLARING, SIST OPPDATERT
        csv.register_dialect('tabs', delimiter='\t')
        read = csv.reader(open(args[0]), dialect='tabs')
        row = read.next()
        if row[0] != 'POSTNR' or row[11] != 'DATAKVALITET':
            raise CommandError("Ser ikkje ut som den korrekte type fila")

        for row in read:
            p = PostNummer()
            p.postnr = row[0].strip().replace(' ', '')
            p.poststad = row[1]
            p.bruksomrade = row[3]
            if (row[4] != ""):
                p.folketal = int(row[4].strip())
            p.bydel = row[5]
            p.kommnr = row[6]
            p.kommune = row[7]
            p.fylke = row[8]
            p.lat = float(row[9])
            p.lon = float(row[10])
            p.datakvalitet = int(row[11])
            if row[-1][0] == "2":
                p.sist_oppdatert = row[-1]

            p.save()
#           print "'%s' '%s' '%s'" % (row, row[6:7], row[7:8])



def stderr(msg):
    if obj:
        obj.stderr.write((unicode(msg) + "\n").encode('utf-8'))
    else:
        print((unicode(msg)).encode('utf-8'))

