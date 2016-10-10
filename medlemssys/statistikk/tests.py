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
from .views import create_overvaking_email


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
                sist_oppdatering=timezone.now() - datetime.timedelta(days=13),
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
