# -*- coding: utf-8 -*-
# vim: ts=4 sts=4 expandtab ai
"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from sets import Set
import datetime

from medlemssys.medlem.models import Medlem, Giro

class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)


class MedlemTest(TestCase):
    medlemar = {}
    year = datetime.date.today().year

    def lagMedlem(self, alder, utmeldt=False, har_betalt=False, name=""):
        if not name:
            name = str(alder)
            if (har_betalt):
                 name += "-betalt"
            if (utmeldt):
                 name += "-utmeld"

        self.medlemar[name] = Medlem(
                        fornamn=name,
                        etternamn="E",
                        fodt=self.year - alder,
                        postnr="5000")

        if (utmeldt):
            self.medlemar[name].utmeldt_dato = datetime.datetime.now()

        self.medlemar[name].save()

        if (har_betalt):
            g = Giro(medlem=self.medlemar[name],
                     belop=80,
                     innbetalt_belop=80,
                     innbetalt=datetime.datetime.now())
            g.save()

        return self.medlemar[name]


    def setUp(self):
        self.lagMedlem(25, utmeldt=False, har_betalt=False)
        self.lagMedlem(25, utmeldt=True,  har_betalt=False)
        self.lagMedlem(25, utmeldt=False, har_betalt=True)
        self.lagMedlem(25, utmeldt=True,  har_betalt=True)

        self.lagMedlem(12, utmeldt=False, har_betalt=False)
        self.lagMedlem(12, utmeldt=True,  har_betalt=False)
        self.lagMedlem(12, utmeldt=False, har_betalt=True)
        self.lagMedlem(12, utmeldt=True,  har_betalt=True)

        self.lagMedlem(26, utmeldt=False, har_betalt=False)
        self.lagMedlem(26, utmeldt=True,  har_betalt=False)
        self.lagMedlem(26, utmeldt=False, har_betalt=True)
        self.lagMedlem(26, utmeldt=True,  har_betalt=True)

        m = self.lagMedlem(23, name="23-betaltifjor")
        m.innmeldt_dato = datetime.date(self.year - 2, 1, 1)
        Giro(medlem=m,
             belop=80,
             innbetalt_belop=80,
             oppretta=datetime.date(self.year - 1, 1, 1),
             innbetalt=datetime.date(self.year - 1, 1, 1)).save()
        m.save()

        m = self.lagMedlem(23, name="23-betaltiforfjor")
        m.innmeldt_dato = datetime.date(self.year - 2, 1, 1)
        Giro(medlem=m,
             belop=80,
             innbetalt_belop=80,
             oppretta=datetime.date(self.year - 2, 1, 1),
             innbetalt=datetime.date(self.year - 2, 1, 1)).save()
        m.save()

        m = self.lagMedlem(23, name="23-innmeldtifjor")
        m.innmeldt_dato = datetime.date(self.year - 1, 1, 1)
        Giro(medlem=m,
             belop=80,
             innbetalt_belop=0,
             oppretta=datetime.date(self.year - 1, 1, 1)).save()
        m.save()

    def test_alle(self):
        """
        Sjekk at me faktisk fær alle når me spyrr om det
        """
        alle = Medlem.objects.alle().values_list('pk', flat=True)
        self.assertEqual(Set([x.pk for x in self.medlemar.values()]), Set(alle))

    def test_ikkje_utmelde(self):
        ikkje_utmelde = Medlem.objects.ikkje_utmelde().values_list('fornamn', flat=True)
        self.assertEqual(Set([
                "12", "12-betalt",
                "25", "25-betalt",
                "26", "26-betalt",
                "23-betaltifjor", "23-innmeldtifjor", "23-betaltiforfjor",
            ]), Set(ikkje_utmelde))

    def test_betalande(self):
        betalande = Medlem.objects.betalande().values_list('fornamn', flat=True)
        self.assertEqual(Set([
                "12-betalt",
                "25-betalt",
                "26-betalt",
            ]), Set(betalande))

    def test_unge(self):
        unge = Medlem.objects.unge().values_list('fornamn', flat=True)
        self.assertEqual(Set([
                "12", "12-betalt",
                "25", "25-betalt",
                "23-betaltifjor", "23-innmeldtifjor", "23-betaltiforfjor",
            ]), Set(unge))

    #def test_potensielt_teljande(self):
    #    potensielt_teljande = Medlem.objects.potensielt_teljande().values_list('fornamn', flat=True)
    #    self.assertEqual(Set([
    #            "12",
    #            "25",
    #        ]), Set(potensielt_teljande))


    def test_teljande(self):
        teljande = Medlem.objects.teljande().values_list('fornamn', flat=True)
        self.assertEqual(Set([
                "12-betalt",
                "25-betalt",
            ]), Set(teljande))

    def test_interessante(self):
        interessante = Medlem.objects.interessante().values_list('fornamn', flat=True)
        self.assertEqual(Set([
                "12-betalt", "12",
                "25-betalt", "25",
                "26-betalt", "26",
                "23-betaltifjor",
            ]), Set(interessante))

    def test_interessante_ifjor(self):
        ifjor = Medlem.objects.interessante(self.year-1).values_list('fornamn', flat=True)
        self.assertEqual(Set([
                "23-betaltifjor", "23-innmeldtifjor", "23-betaltiforfjor",
            ]), Set(ifjor))
