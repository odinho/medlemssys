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

from django.core.management.base import BaseCommand, CommandError

from medlemssys.innhenting.management import nmu
from medlemssys.medlem.models import update_denormalized_fields
from medlemssys.statistikk.views import send_overvakingar
from medlemssys.statistikk.views import update_lokallagstat


class Command(BaseCommand):
    help = "Importerer medlemane inn i databasen"
    force_update = False

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '--medlem', dest='medlem_csv',
            help="fil å lesa medlemar frå")
        parser.add_argument(
            '--lokallag', dest='lokallag_csv',
            help="fil å lesa lokallag frå")
        parser.add_argument(
            '--betaling', dest='betaling_csv',
            help="fil å lesa betalingar frå")
        parser.add_argument(
            '--force-update',
            action='store_true',
            dest='force_update',
            default=False,
            help="tving gjennom oppdatering av giroar")
        parser.add_argument(
            '--importer',
            dest='importer',
            default='guess_csv',
            help="importeringssystem (guess_csv, nmu_access eller nmu_mamut)")

    def handle(self, *args, **options):
        if options['force_update']:
            self.force_update = True

        if options['importer'] == 'guess_csv':
            imp = nmu.GuessingCSVImporter()
        elif options['importer'] == 'nmu_access':
            imp = nmu.AccessImporter()
        elif options['importer'] == 'nmu_mamut':
            imp = nmu.MamutImporter()
        else:
            raise CommandError(
                "Importeren finst ikkje ({0})"
                .format(options['importer']).encode('utf8'))

        if not (options['lokallag_csv'] or options['medlem_csv'] or
                options['betaling_csv']):
            self.stdout.write(u"Ingen filer valt, ingen importering skjer.")
        if options['lokallag_csv']:
            for i in imp.import_lag(options['lokallag_csv']).values():
                self.stdout.write(u"Lag: {0}\n".format(i))

        if options['medlem_csv']:
            for i in imp.import_medlem(options['medlem_csv']):
                self.stdout.write(u"Medlem: {0}\n".format(i))

        if options['betaling_csv']:
            for i in imp.import_bet(options['betaling_csv'],
                                    force_update=self.force_update):
                self.stdout.write(u"Betaling: {0}\n".format(i))

        update_denormalized_fields()
        update_lokallagstat()
        send_overvakingar()
