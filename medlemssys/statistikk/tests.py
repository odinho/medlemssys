# -*- coding: utf-8 -*-
# vim: ts=4 sts=4 expandtab ai

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
import datetime
import re

from django.test import TestCase
from django.utils import timezone

from medlemssys.medlem.tests import lagTestMedlemar
from medlemssys.medlem.models import LokallagOvervaking, Lokallag
from .views import _get_overvakingar
from .views import create_overvaking_email
from .views import update_lokallagstat


class OvervakingGenerationTest(TestCase):
    def setUp(self):
        self.lokallag = Lokallag.objects.create(namn='Lokallag')
        self.medlemar = lagTestMedlemar()
        weeks_ago = timezone.now() - datetime.timedelta(days=14)
        LokallagOvervaking.objects.create(
            epost='test@s0.no', lokallag=self.lokallag)
        LokallagOvervaking.objects.update(sist_oppdatert=weeks_ago)
        self.overvaking = LokallagOvervaking.objects.get()
        self.medlemar['12-betalt'].oppretta = weeks_ago
        self.medlemar['12-betalt'].lokallag = self.lokallag
        self.medlemar['12-betalt'].save()
        update_lokallagstat(weeks_ago)

    def test_get_overvakingar(self):
        self.medlemar['25'].lokallag = self.lokallag
        self.medlemar['25'].save()
        ctx_list = []
        epost_seq, overvak, sist_oppdatering, ctx = next(_get_overvakingar())
        keys = ['vekkflytta_medlem', 'endra_medlem', 'ukjend_endring',
                'nye_medlem', 'utmeld_medlem', 'tilflytta_medlem',
                'nye_infofolk']
        self.assertEquals(ctx.keys(), keys)
        self.assertEquals([len(ctx[k]) for k in keys], [0, 0, 0, 1, 0, 0, 0])
        self.assertEquals(ctx['nye_medlem'][0].fornamn, '25')


class OvervakingEpostTest(TestCase):
    def setUp(self):
        self.medlemar = lagTestMedlemar()

    def test_nye_medlem(self):
        m12 = self.medlemar["12"]
        m25b = self.medlemar["25-betalt"]
        msg = create_overvaking_email(
                ['test@s0.no'],
                'Testovervaking',
                self.medlemar.values()[0].lokallag,
                sist_oppdatering=timezone.now() -
                    datetime.timedelta(days=13),
                nye_medlem=(m12, m25b))
        txt = msg.alternatives[0][0]
        re_epost = (r'.*To nye medlemar.*'
            r'<td>{m12} <td>{m12.fodt} <td>Nei .*'
            r'<td>{m25b} <td>{m25b.fodt} <td>Ja .*'
            ''.format(m12=m12, m25b=m25b))
        self.assertRegexpMatches(txt, re.compile(re_epost, re.DOTALL))

    def test_endra_medlem(self):
        m12 = self.medlemar["12"]
        m12.changed = [('test', '1', '2'), ('thing', 'a', 'b')]
        m25b = self.medlemar["25-betalt"]
        msg = create_overvaking_email(
                ['test@s0.no'],
                'Testovervaking',
                self.medlemar.values()[0].lokallag,
                sist_oppdatering=timezone.now() - datetime.timedelta(days=13),
                endra_medlem=(m12, m25b))
        txt = msg.alternatives[0][0]
        re_epost = (
            r'.*To medlemar med endringar.*'
            r'<li><strong>{m12}</strong>.*'
            r'<th.*>test <td>1 <td>2.*'
            r'<th.*>thing <td>a <td>b.*'
            r'<li><strong>{m25b}</strong>.*'
            ''.format(m12=m12, m25b=m25b))
        self.assertRegexpMatches(txt, re.compile(re_epost, re.DOTALL))

    def test_utmeld_medlem(self):
        m12 = self.medlemar["12-utmeld"]
        m25b = self.medlemar["25-betalt-utmeld"]
        msg = create_overvaking_email(
                ['test@s0.no'],
                'Testovervaking',
                self.medlemar.values()[0].lokallag,
                sist_oppdatering=timezone.now() - datetime.timedelta(days=13),
                utmeld_medlem=(m12, m25b))
        txt = msg.alternatives[0][0]
        re_epost = (r'.*To utmelde medlemar.*'
            r'<td>{m12} <td>{m12.fodt} <td>Nei .*'
            r'<td>{m25b} <td>{m25b.fodt} <td>Ja .*'
            ''.format(m12=m12, m25b=m25b))
        self.assertRegexpMatches(txt, re.compile(re_epost, re.DOTALL))

    def test_tilflytta_medlem(self):
        m12 = self.medlemar["12"]
        m25b = self.medlemar["25-betalt"]
        msg = create_overvaking_email(
                ['test@s0.no'],
                'Testovervaking',
                self.medlemar.values()[0].lokallag,
                sist_oppdatering=timezone.now() - datetime.timedelta(days=13),
                tilflytta_medlem=(m12, m25b))
        txt = msg.alternatives[0][0]
        re_epost = (r'.*To nytilflytta medlemar.*'
            r'<td>{m12} <td>{m12.fodt} <td>Nei .*'
            r'<td>{m25b} <td>{m25b.fodt} <td>Ja .*'
            ''.format(m12=m12, m25b=m25b))
        self.assertRegexpMatches(txt, re.compile(re_epost, re.DOTALL))

    def test_vekkflytta_medlem(self):
        m12 = self.medlemar["12"]
        m25b = self.medlemar["25-betalt"]
        msg = create_overvaking_email(
                ['test@s0.no'],
                'Testovervaking',
                self.medlemar.values()[0].lokallag,
                sist_oppdatering=timezone.now() - datetime.timedelta(days=13),
                vekkflytta_medlem=(m12, m25b))
        txt = msg.alternatives[0][0]
        re_epost = (ur'.*To fråflytta medlemar.*'
            r'<td>{m12} <td>{m12.fodt} <td>Nei .*'
            r'<td>{m25b} <td>{m25b.fodt} <td>Ja .*'
            ''.format(m12=m12, m25b=m25b))
        self.assertRegexpMatches(txt, re.compile(re_epost, re.DOTALL))
