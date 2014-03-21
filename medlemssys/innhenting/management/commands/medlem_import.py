#!/usr/bin/env python
# vim: fileencoding=utf-8 shiftwidth=4 tabstop=4 expandtab softtabstop=4 ai

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
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from innhenting.management import nmu
from medlem.models import update_denormalized_fields
from statistikk.views import update_lokallagstat, send_overvakingar


class Command(BaseCommand):
    args = '[ medlem.csv [ lokallag.csv [ betaling.csv ] ] ]'
    help = "Importerer medlemane inn i databasen"
    force_update = False
    option_list = BaseCommand.option_list + (
        make_option('-f', '--force-update',
            action='store_true',
            dest='force_update',
            default=False,
            help="tving gjennom oppdatering av giroar"),
        make_option('--importer',
            dest='importer',
            default='nmu_access',
            help="importeringssystem (nmu_access eller nmu_mamut)"),
        )

    def handle(self, *args, **options):
        if options['force_update']:
            self.force_update = True

        medlem_csv = self.get_filename(args, 0, 'MEDLEM_CSV', 'nmu-medl.csv')
        lag_csv = self.get_filename(args, 1, 'LAG_CSV', 'nmu-lag.csv')
        bet_csv = self.get_filename(args, 2, 'GIRO_CSV', 'nmu-bet.csv')

        if options['importer'] == 'nmu_access':
            imp = nmu.AccessImporter(medlem_csv, lag_csv, bet_csv)
        elif options['importer'] == 'nmu_mamut':
            imp = nmu.MamutImporter(medlem_csv, lag_csv, bet_csv)
        else:
            raise CommandError("Importeren finst ikkje ({0})".format(options['importer']).encode('utf8'))

        for i in imp.import_lag().values():
            self.stdout.write(u"Lag: {0}\n".format(i))

        for i in imp.import_medlem():
            self.stdout.write(u"Medlem: {0}\n".format(i))

        for i in imp.import_bet(force_update=self.force_update):
            self.stdout.write(u"Betaling: {0}\n".format(i))

        update_denormalized_fields()
        update_lokallagstat()
        send_overvakingar()

    def get_filename(self, args, num, setting, fallback):
        if len(args) > num:
            fn = args[num]
        else:
            fn = getattr(settings, setting, fallback)
        if not os.path.isfile(fn):
            raise CommandError("Fila finst ikkje ({0})".format(fn).encode('utf8'))
        return fn
