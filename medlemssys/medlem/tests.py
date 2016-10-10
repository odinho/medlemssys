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
import datetime

from django.contrib.auth.models import User
from django.test import Client
from django.test import TestCase
from django.utils import timezone

from medlemssys.medlem import models
from medlemssys.medlem.models import Giro
from medlemssys.medlem.models import Medlem


def lagMedlem(alder, utmeldt=False, har_betalt=False, name="", **kwargs):
    year = datetime.date.today().year
    if not name:
        name = str(alder)
        if (har_betalt):
             name += "-betalt"
        if (utmeldt):
             name += "-utmeld"

    medlem = Medlem(fornamn=name, etternamn="E", fodt=year - alder,
                    postnr="5000", **kwargs)

    if (utmeldt):
        medlem.utmeldt_dato = datetime.date.today()

    medlem.save()

    if (har_betalt):
        g = Giro(medlem=medlem,
                 belop=80,
                 innbetalt_belop=80,
                 innbetalt=timezone.now())
        g.save()

    return medlem

def lagTestMedlemar(**extra_kwargs):
    medlemar = {}
    year = datetime.date.today().year

    def opprett_og_lagra_medlem(*args, **kwargs):
        kwargs.update(extra_kwargs)
        medlem = lagMedlem(*args, **kwargs)
        medlemar[medlem.fornamn] = medlem
        return medlem

    opprett_og_lagra_medlem(25, utmeldt=False, har_betalt=False)
    opprett_og_lagra_medlem(25, utmeldt=True,  har_betalt=False)
    opprett_og_lagra_medlem(25, utmeldt=False, har_betalt=True)
    opprett_og_lagra_medlem(25, utmeldt=True,  har_betalt=True)

    opprett_og_lagra_medlem(12, utmeldt=False, har_betalt=False)
    opprett_og_lagra_medlem(12, utmeldt=True,  har_betalt=False)
    opprett_og_lagra_medlem(12, utmeldt=False, har_betalt=True)
    opprett_og_lagra_medlem(12, utmeldt=True,  har_betalt=True)

    opprett_og_lagra_medlem(26, utmeldt=False, har_betalt=False)
    opprett_og_lagra_medlem(26, utmeldt=True,  har_betalt=False)
    opprett_og_lagra_medlem(26, utmeldt=False, har_betalt=True)
    opprett_og_lagra_medlem(26, utmeldt=True,  har_betalt=True)

    m = opprett_og_lagra_medlem(23, name="23-betaltifjor")
    m.innmeldt_dato = datetime.date(year - 2, 1, 1)
    Giro(medlem=m,
         belop=80,
         innbetalt_belop=80,
         gjeldande_aar=year - 1,
         oppretta=datetime.date(year - 1, 1, 1),
         innbetalt=datetime.date(year - 1, 1, 1)).save()
    m.save()

    m = opprett_og_lagra_medlem(23, name="23-betaltiforfjor")
    m.innmeldt_dato = datetime.date(year - 2, 1, 1)
    Giro(medlem=m,
         belop=80,
         innbetalt_belop=80,
         gjeldande_aar=year - 2,
         oppretta=datetime.date(year - 2, 1, 1),
         innbetalt=datetime.date(year - 2, 1, 1)).save()
    m.save()

    m = opprett_og_lagra_medlem(23, name="23-innmeldtifjor")
    m.innmeldt_dato = datetime.date(year - 1, 1, 1)
    Giro(medlem=m,
         belop=80,
         innbetalt_belop=0,
         gjeldande_aar=year - 1,
         oppretta=datetime.date(year - 1, 1, 1)).save()
    m.save()

    m = opprett_og_lagra_medlem(23, name="23-innmeldtifjor-utmeldtiaar")
    m.innmeldt_dato = datetime.date(year - 1, 1, 1)
    m.utmeldt_dato = datetime.date(year, 1, 1)
    Giro(medlem=m,
         belop=80,
         innbetalt_belop=0,
         gjeldande_aar=year - 1,
         oppretta=datetime.date(year - 1, 1, 1)).save()
    m.save()

    m = opprett_og_lagra_medlem(23, name="23-innmeldtiforfjor-utmeldtnesteaar")
    m.innmeldt_dato = datetime.date(year - 2, 1, 1)
    m.utmeldt_dato = datetime.date(year + 1, 1, 1)
    m.save()

    m = opprett_og_lagra_medlem(23, name="23-betaltifjor-utmeldtnesteaar")
    m.innmeldt_dato = datetime.date(year - 2, 1, 1)
    m.utmeldt_dato = datetime.date(year + 1, 1, 1)
    Giro(medlem=m,
         belop=80,
         innbetalt_belop=80,
         gjeldande_aar=year - 1,
         oppretta=datetime.date(year - 1, 1, 1),
         innbetalt=datetime.date(year - 1, 1, 1)).save()
    m.save()

    m = opprett_og_lagra_medlem(23, har_betalt=True, name="23-betalt-utmeldtnesteaar")
    m.utmeldt_dato = datetime.date(year + 1, 1, 2)
    m.save()

    # innmeldt og utmeldt i fjor
    # innmeldt i fjor, men utmeldt no
    # utmeldt til neste år

    return medlemar


class MedlemTest(TestCase):

    def test_utmeldt_delete_unpaid_giro_on_denormalized(self):
        # Unpaid giros are deleted after member is utmeldt and
        # update_denormalized_fields has run
        m = lagMedlem(29, har_betalt=True)
        g = Giro(medlem=m, belop=10)
        g.save()
        self.assertEqual(
            [g.belop for g in m.giroar.all()], [10, 80])
        m.utmeldt_dato = datetime.date.today()
        m.save()
        models.update_denormalized_fields()
        self.assertEqual(
            [g.belop for g in m.giroar.all()], [80])

    def test_utmeldt_add_unpaid_giro(self):
        # Adding new (unpaid) giro to utmeldt member doesn't
        # actually get saved
        m = lagMedlem(29, har_betalt=True, utmeldt=True)
        g = Giro(medlem=m, belop=10)
        g.save()
        self.assertEqual(
            [g.belop for g in m.giroar.all()], [80])

    def test_utmeldt_add_paid_giro(self):
        # Adding new (unpaid) giro to utmeldt member doesn't
        # actually get saved
        m = lagMedlem(29, har_betalt=True, utmeldt=True)
        g = Giro(medlem=m, belop=20,
                 innbetalt_belop=20, innbetalt=timezone.now())
        g.save()
        self.assertEqual(
            [g.belop for g in m.giroar.all()], [20, 80])


class MedlemManagerTest(TestCase):
    year = datetime.date.today().year

    def setUp(self):
        self.medlemar = lagTestMedlemar()

    def test_alle(self):
        """
        Sjekk at me faktisk fær alle når me spyrr om det
        """
        alle = Medlem.objects.alle().values_list('pk', flat=True)
        self.assertEqual(set([x.pk for x in self.medlemar.values()]), set(alle))

    def test_utmelde(self):
        utmelde = Medlem.objects.utmelde().values_list('fornamn', flat=True)
        self.assertEqual(set([
                "12-utmeld", "12-betalt-utmeld",
                "25-utmeld", "25-betalt-utmeld",
                "26-utmeld", "26-betalt-utmeld",
                "23-innmeldtifjor-utmeldtiaar",
            ]), set(utmelde))

    def test_ikkje_utmelde(self):
        ikkje_utmelde = Medlem.objects.ikkje_utmelde().values_list('fornamn', flat=True)
        self.assertEqual(set([
                "12", "12-betalt",
                "25", "25-betalt",
                "26", "26-betalt",
                "23-betaltifjor", "23-innmeldtifjor", "23-betaltiforfjor",
                "23-betalt-utmeldtnesteaar",
                "23-betaltifjor-utmeldtnesteaar",
                "23-innmeldtiforfjor-utmeldtnesteaar",
            ]), set(ikkje_utmelde))

    def test_betalande(self):
        betalande = Medlem.objects.betalande().values_list('fornamn', flat=True)
        self.assertEqual(set([
                "12-betalt",
                "25-betalt",
                "26-betalt",
                "23-betalt-utmeldtnesteaar",
            ]), set(betalande))

    def test_unge(self):
        unge = Medlem.objects.unge().values_list('fornamn', flat=True)
        self.assertEqual(set([
                "12", "12-betalt",
                "25", "25-betalt",
                "23-betaltifjor", "23-innmeldtifjor", "23-betaltiforfjor",
                "23-betalt-utmeldtnesteaar",
                "23-betaltifjor-utmeldtnesteaar",
                "23-innmeldtiforfjor-utmeldtnesteaar",
            ]), set(unge))

    #def test_potensielt_teljande(self):
    #    potensielt_teljande = Medlem.objects.potensielt_teljande().values_list('fornamn', flat=True)
    #    self.assertEqual(set([
    #            "12",
    #            "25",
    #        ]), set(potensielt_teljande))


    def test_teljande(self):
        teljande = Medlem.objects.teljande().values_list('fornamn', flat=True)
        self.assertEqual(set([
                "12-betalt",
                "25-betalt",
                "23-betalt-utmeldtnesteaar",
            ]), set(teljande))

    def test_interessante(self):
        interessante = Medlem.objects.interessante().values_list('fornamn', flat=True)
        self.assertEqual(set([
                "12-betalt", "12",
                "25-betalt", "25",
                "26-betalt", "26",
                "23-betaltifjor",
                "23-betalt-utmeldtnesteaar",
                "23-betaltifjor-utmeldtnesteaar",
            ]), set(interessante))

    def test_interessante_ifjor(self):
        ifjor = Medlem.objects.interessante(self.year-1).values_list('fornamn', flat=True)
        self.assertEqual(set([
                "23-betaltifjor", "23-innmeldtifjor", "23-betaltiforfjor",
                "23-betaltifjor-utmeldtnesteaar",
                "23-innmeldtifjor-utmeldtiaar",
            ]), set(ifjor))


class WebTest(TestCase):
    def setUp(self):
        lagTestMedlemar()
        self.client = Client()
        user = User.objects.create_user('test_user', password='pass')
        self.client.force_login(user)

    def test_api_get_members(self):
        response = self.client.get('/api/get_members.json')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(len(response.json()), Medlem.objects.count())

    def test_api_get_members_search_term(self):
        response = self.client.get('/api/get_members.json?term=23-')
        self.assertEquals(response.status_code, 200)

        result = response.json()[0]
        checks = dict(bet=['2016'], lokallag='(ingen)',
                      namn='23-betalt-utmeldtnesteaar E', alder=23)
        for key, value in checks.items():
            self.assertEquals(result[key], value)
        self.assertEquals(len(response.json()), 7)
