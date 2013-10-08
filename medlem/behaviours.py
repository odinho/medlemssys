# -*- coding: utf-8 -*-
# vim: ts=4 sts=4 expandtab ai
from datetime import date
from django.db.models import Q
from django.db.models.query import QuerySet

class MedlemQuerySetBase(QuerySet):
    """Inherit from this base, call the class MedlemQuerySet and
    refer to it from BEHAVIOURS_MODULE in settings"""
    ung_alder = None

    def __init__(self, *args, **kwargs):
        assert self.ung_alder
        super(MedlemQuerySetBase, self).__init__(*args, **kwargs)

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

    def nye(self, year=date.today().year):
        """Nyinnmelde medlem i dette året"""
        return self.ikkje_utmelde(year).filter(innmeldt_dato__year=year).distinct()

    def teljande_nye(self, year=date.today().year):
        """Nyinnmelde medlem som er teljande"""
        return self.nye(year) & self.teljande(year)

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
        from models import PostNummer
        nr = PostNummer.objects.filter(fylke=fylke).values_list('postnr', flat=True)
        return self.alle().filter(
                   postnr__in=nr.values_list('postnr', flat=True).distinct())

    def kommune(self, kommune, fylke=None):
        """Medlem som ikkje er eksplisitt utmelde"""
        from models import PostNummer
        nr = PostNummer.objects.filter(kommune=kommune)
        if fylke:
            nr = nr.filter(fylke=fylke)
        return self.alle().filter(
                   postnr__in=nr.values_list('postnr', flat=True).distinct())
