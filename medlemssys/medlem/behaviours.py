# -*- coding: utf-8 -*-
# vim: ts=4 sts=4 expandtab ai

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

from collections import namedtuple
from datetime import date

from django.db.models import F
from django.db.models import Q
from django.db.models.query import QuerySet

from .models import PostNummer


Lookup = namedtuple('Lookup', 'key title filter')

MEDLEM_LOOKUPS = [
    Lookup('ikkje_utmelde', "Ikkje utmelde",
           lambda qs: qs.ikkje_utmelde()),
    Lookup('interessante', "Interessante",
           lambda qs: qs.interessante()),
    Lookup('betalande', "Betalande",
           lambda qs: qs.betalande()),
    Lookup('betalandeifjor', "Betalande (i fjor)",
           lambda qs: qs.betalande(date.today().year - 1)),
    Lookup('nye', "Nye i år",
           lambda qs: qs.nye()),
    Lookup('nye_betalande', "Nye i år (betalande)",
           lambda qs: qs.betalande_nye()),
]

def strange_giro(queryset):
    not_fully_paid = (
        ~Q(innbetalt_belop=0) & ~Q(innbetalt_belop=F('belop')))
    paid_but_not_finished = Q(innbetalt__isnull=False) & ~Q(status='F')
    unpaid_but_finished = (
        Q(innbetalt__isnull=True) | Q(innbetalt_belop=0)
            & Q(status='F'))
    return queryset.filter(not_fully_paid |
                           paid_but_not_finished |
                           unpaid_but_finished)

GIRO_LOOKUPS = [
    Lookup('strange', "Rare/feil giroar", strange_giro),
]


class MedlemQuerySet(QuerySet):
    """Inherit from this base, call the class MedlemQuerySet and
    refer to it from BEHAVIOURS_MODULE in settings"""

    def alle(self):
        """Alle oppføringar i registeret"""
        if getattr(self, 'core_filters', None):
            return self.filter(**self.core_filters)
        return self

    def ikkje_utmelde(self, year=date.today().year):
        """Medlem som ikkje er eksplisitt utmelde"""
        return self.alle().filter(
            Q(utmeldt_dato__isnull=True) | Q(utmeldt_dato__gte=date(year+1, 1, 1))
        )

    def utmelde(self, year=date.today().year):
        """Medlem som er utmelde"""
        return self.alle().filter(
            utmeldt_dato__isnull=False, utmeldt_dato__lt=date(year+1, 1, 1)
        )

    def betalande(self, year=date.today().year):
        """Medlem med ein medlemspengeinnbetaling inneverande år"""
        return self.ikkje_utmelde(year) \
            .filter(
                giroar__gjeldande_aar=year,
                giroar__innbetalt__isnull=False
            ).distinct()

    def nye(self, year=date.today().year):
        """Nyinnmelde medlem i dette året"""
        return self.ikkje_utmelde(year).filter(innmeldt_dato__year=year).distinct()

    def betalande_nye(self, year=date.today().year):
        """Nyinnmelde medlem som har betalt"""
        return self.nye(year) & self.betalande(year)

    def interessante(self, year=date.today().year):
        """Medlem som har betalt i år eller i fjor."""
        return self.ikkje_utmelde(year) \
            .filter(
                Q(innmeldt_dato__year=year) |
                Q(giroar__gjeldande_aar=year,
                  giroar__innbetalt__isnull=False) |
                Q(giroar__gjeldande_aar=year-1,
                  giroar__innbetalt__isnull=False)
            ).distinct()

    # Postnummer
    def fylke(self, fylke):
        """Medlem som ikkje er eksplisitt utmelde"""
        nr = PostNummer.objects.filter(fylke=fylke).values_list('postnr', flat=True)
        # Converting the QuerySet __in to a list because of a MySQL performance issue
        return self.alle().filter(
                   postnr__in=list(nr.values_list('postnr', flat=True).distinct()))

    def kommune(self, kommune, fylke=None):
        """Medlem som ikkje er eksplisitt utmelde"""
        nr = PostNummer.objects.filter(kommune=kommune)
        if fylke:
            nr = nr.filter(fylke=fylke)
        # Converting the QuerySet __in to a list because of a MySQL performance issue
        return self.alle().filter(
                   postnr__in=list(nr.values_list('postnr', flat=True).distinct()))
