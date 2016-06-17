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


from django.core.management.base import BaseCommand

from medlemssys.medlem.models import update_denormalized_fields
from medlemssys.statistikk.views import send_overvakingar
from medlemssys.statistikk.views import update_lokallagstat


class Command(BaseCommand):
    help = "Do nightly chores"

    def handle(self, *args, **options):
        update_denormalized_fields()
        update_lokallagstat()
        send_overvakingar()
