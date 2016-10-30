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

from __future__ import unicode_literals

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from medlemssys.medlem.models import Medlem
from medlemssys.medlem.tests import lagTestMedlemar


class MedlemInnmelding(APITestCase):
    def create_data(self, **kw):
        kw.update(dict(
            token=settings.INNMELDING_TOKEN, postnr='5003', fodt=2000))
        return kw

    def test_disallow_read(self):
        r = self.client.get(reverse('api-innmelding'))
        self.assertEquals(status.HTTP_405_METHOD_NOT_ALLOWED, r.status_code)

    def test_require_some_fields(self):
        r = self.client.post(reverse('api-innmelding'), {})
        self.assertEquals(status.HTTP_400_BAD_REQUEST, r.status_code)
        self.assertEquals(r.data.keys(), ['postnr', 'fodt', 'token'])

    def test_create(self):
        r = self.client.post(reverse('api-innmelding'),
            self.create_data(fornamn='Å', etternamn='L'))
        self.assertEquals(status.HTTP_201_CREATED, r.status_code)
        self.assertEquals(r.data, {
            'fornamn': 'Å', 'etternamn': 'L', 'fodt': 2000, 'postnr': '5003',
            'stad': '?', 'mobnr': '', 'epost': ''
        })
        self.assertEquals(
           Medlem.objects.values_list(
               'etternamn', 'status', 'innmeldingstype')[0],
           ('L', 'I', 'H'))

    def test_namn_not_empty(self):
        r = self.client.post(
            reverse('api-innmelding'), self.create_data(namn=''))
        self.assertEquals(r.data, {
            'non_field_errors': ['Specify either fornamn+etternamn, or namn']})

    def test_cors_nothing_wo_origin(self):
        res = self.client.post(
            reverse('api-innmelding'), self.create_data(namn='x'))
        self.assertEquals(res.has_header('Access-Control-Allow-Origin'), False)

    def test_cors_allowed(self):
        res = self.client.post(
            reverse('api-innmelding'), self.create_data(namn='x'),
            HTTP_ORIGIN='http://example.com:80')
        self.assertEquals(res.has_header('Access-Control-Allow-Origin'), True)
        self.assertEquals(
            res['Access-Control-Allow-Origin'], 'http://example.com:80')

    def test_cors_disallowed(self):
        res = self.client.post(
            reverse('api-innmelding'), self.create_data(namn='x'),
            HTTP_ORIGIN='http://evil.example.com:80')
        self.assertEquals(res.has_header('Access-Control-Allow-Origin'), False)

    def test_namn(self):
        tests = [
          ('Å L', 'Å', 'L'),
          ('Test Foo Bar', 'Test Foo', 'Bar'),
          ('Test Foo Bar Baz', 'Test Foo Bar', 'Baz'),
          ('Test', 'Test', ''),
          ('Test', 'Test', ''),
          #('Test Foo Bar Baz', 'Test Foo', 'Bar Baz'),
        ]
        for full_n, fn, ln in tests:
            r = self.client.post(reverse('api-innmelding'),
                self.create_data(namn=full_n))
            self.assertEquals(
                [r.data[v] for v in ['fornamn', 'etternamn']],
                [fn, ln])

    def test_next_redir(self):
        r = self.client.post(
            reverse('api-innmelding') + '?next=http://example.com/b',
            self.create_data(namn='x'))
        self.assertEquals(r.status_code, 302)
        self.assertEquals(r.content, '')

    def test_next_disallow_redir(self):
        r = self.client.post(
            reverse('api-innmelding') + '?next=http://evil.com/b',
            self.create_data(namn='x'))
        self.assertEquals(r.status_code, 201)


class MedlemAPI(APITestCase):
    def setUp(self):
        self.m = lagTestMedlemar()

    def test_disallow_read(self):
        r = self.client.get('/api/medlem/')
        self.assertEquals(r.status_code, 401)
        r = self.client.post('/api/medlem/', {})
        self.assertEquals(r.status_code, 401)
        r = self.client.get('/api/medlem/1/')
        self.assertEquals(r.status_code, 401)
        r = self.client.put('/api/medlem/1/')
        self.assertEquals(r.status_code, 401)
        r = self.client.delete('/api/medlem/1/')
        self.assertEquals(r.status_code, 401)

    def test_disallow_non_staff(self):
        user = User.objects.create_user(username='user')
        self.client.force_authenticate(user)
        r = self.client.get('/api/medlem/')
        self.assertEquals(r.status_code, 403)
        r = self.client.get('/api/medlem/1/')
        self.assertEquals(r.status_code, 403)

    def test_medlem_list(self):
        user = User.objects.create_user(username='user', is_staff=True)
        self.client.force_authenticate(user)
        r = self.client.get('/api/medlem/')
        self.assertEquals(r.status_code, 200)
        self.assertEquals(len(r.data), 19)

    def test_medlem_single(self):
        user = User.objects.create_user(username='user', is_staff=True)
        self.client.force_authenticate(user)
        m = self.m['25-betalt']
        r = self.client.get('/api/medlem/%d/' % m.pk)
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.data['fornamn'], '25-betalt')
        self.assertEquals(r.data['etternamn'], 'E')
        self.assertEquals(r.data.keys(), [
             'url', 'fornamn', 'mellomnamn', 'etternamn', 'fodt',
             'postadr', 'ekstraadr', 'postnr', 'epost', 'mobnr',
             'borteadr', 'bortepostnr'])

    def test_medlem_patch(self):
        user = User.objects.create_user(username='user', is_staff=True)
        self.client.force_authenticate(user)
        m = self.m['12']
        r = self.client.patch('/api/medlem/%d/' % m.pk, {'etternamn': 'Test'})
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.data['fornamn'], '12')
        self.assertEquals(r.data['etternamn'], 'Test')
        self.assertEquals(m.etternamn, 'E')
        m.refresh_from_db()
        self.assertEquals(m.etternamn, 'Test')
