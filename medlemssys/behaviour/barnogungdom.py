# -*- coding: utf-8 -*-
# Copyright 2009-2016 Odin Hørthe Omdal

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

from datetime import date

from medlemssys.medlem.behaviours import Lookup
from medlemssys.medlem.behaviours import MedlemQuerySet
from medlemssys.medlem.models import Medlem

from .base import BaseBehaviour


class BarnOgUngdomMedlemQuerySet(MedlemQuerySet):
    ung_alder = 25

    def unge(self, year=date.today().year):
        """Medlem rekna som unge (altso i teljande alder)"""
        return self.ikkje_utmelde(year) \
            .filter(
                fodt__gte = year - self.ung_alder
            )

    def potensielt_teljande(self, year=date.today().year):
        return self.unge(year).filter(postnr__gt="0000", postnr__lt="9999") \
            .exclude(giroar__gjeldande_aar=year,
                giroar__innbetalt__isnull=False)

    def teljande(self, year=date.today().year):
        """Medlem i teljande alder, med postnr i Noreg og med betalte
        medlemspengar"""
        return self.betalande(year) & self.unge(year).distinct().filter(postnr__gt="0000", postnr__lt="9999")

    def teljande_nye(self, year=date.today().year):
        """Nyinnmelde medlem som er teljande"""
        return self.nye(year) & self.teljande(year)


class Behaviour(BaseBehaviour):
    queryset_class = BarnOgUngdomMedlemQuerySet
    medlem_ui_filters = BaseBehaviour.medlem_ui_filters + [
        Lookup('teljande', "Teljande",
               lambda qs: qs.teljande()),
        Lookup('potensielle', "Potensielt teljande",
               lambda qs: qs.potensielt_teljande()),
        Lookup('nye_teljande', "Teljande (nye i år)",
               lambda qs: qs.teljande(date.today().year - 1)),
        Lookup('teljandeifjor', "Teljande (i fjor)",
               lambda qs: qs.teljande(date.today().year - 1)),
    ]
    giro_ui_filters = BaseBehaviour.giro_ui_filters + [
        Lookup('teljandeifjor', "Teljande (i fjor)",
               lambda qs: (
                   qs.filter(medlem__in=(Medlem.objects.teljande()
                                         .values_list('pk', flat=True)))
                   .filter(gjeldande_aar=date.today().year))),
        Lookup('teljande', "Teljande (i år)",
               lambda qs: (
                   qs.filter(medlem__in=(Medlem.objects.teljande(
                                             date.today().year - 1)
                                         .values_list('pk', flat=True)))
                   .filter(gjeldande_aar=date.today().year - 1))),
        Lookup('potensieltteljande', "Potensielt teljande (i år)",
               lambda qs: (
                   qs.filter(medlem__in=(Medlem.objects.potensielt_teljande()
                                         .values_list('pk', flat=True)))
                   .filter(gjeldande_aar=date.today().year))),
    ]
