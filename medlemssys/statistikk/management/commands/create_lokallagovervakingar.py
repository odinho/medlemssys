#!/usr/bin/env python
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

from optparse import make_option

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from medlemssys.medlem.models import LokallagOvervaking, Lokallag


class Command(BaseCommand):
    args = '[ delete ]'
    help = 'Opprett (og reinsk inaktive) standard LokallagsOvervakingar'
    option_list = BaseCommand.option_list + (
        make_option('-d', '--delete',
            action='store_true',
            dest='delete',
            default=False,
            help=u"""Slettar alle lokallagsovervakingar som ikkje er spesielle på nokon helst måte (altso: truleg automatisk oppretta)."""),
        )

    def handle(self, *args, **options):
        if options['delete']:
            self.delete_lokallagovervakingar()
        else:
            self.clean_stale()
            self.create_lokallagovervakingar()

    @transaction.atomic
    def clean_stale(self):
        stale = LokallagOvervaking.objects.filter(
            lokallag__aktivt=False,
            epost='',
            medlem__isnull=True,
            deaktivert__isnull=True)
        for lo in stale:
            self.out('Deactivating ' + unicode(lo))
            lo.deaktivert = timezone.now()
            lo.save()

    @transaction.atomic
    def create_lokallagovervakingar(self):
        new = Lokallag.objects.filter(aktivt=True, lokallagovervaking__isnull=True)
        for n in new:
            lo = LokallagOvervaking(lokallag=n)
            lo.save()
            self.out(u"{}: {}".format(
                    unicode(lo), unicode(lo.epostar())))

    def delete_lokallagovervakingar(self):
        """Slettar alle lokallagsovervakingar som ikkje er spesielle på nokon
        helst måte (altso: truleg automatisk oppretta)."""
        num = LokallagOvervaking.objects.filter(
            epost='',
            medlem__isnull=True).delete()
        self.out("Sletta {} overvakingar.".format(num))

    def err(self, msg):
        self.stderr.write((unicode(msg) + "\n").encode('utf-8'))
    def out(self, msg):
        self.stdout.write((unicode(msg) + "\n").encode('utf-8'))
