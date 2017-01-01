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
from django.core.exceptions import ValidationError
from rest_framework import serializers

from medlemssys.medlem.models import Medlem


class InnmeldingMedlemSerializer(serializers.ModelSerializer):
    namn = serializers.CharField(write_only=True, required=False)
    token = serializers.CharField(write_only=True)

    class Meta:
        fields = (
            'fornamn', 'etternamn', 'postnr', 'fodt', 'epost', 'mobnr',
            'stad', 'namn', 'token')
        model = Medlem
        extra_kwargs = {
           'fodt': {'required': True},
           'fornamn': {'required': False},
           'etternamn': {'required': False},
           'stad': {'read_only': True},
        }

    def validate(self, data):
        if not settings.INNMELDING_TOKEN and not settings.DEBUG or (
                data.pop('token', None) != settings.INNMELDING_TOKEN):
            raise ValidationError(
                'Invalid innmelding token')
        if not ('fornamn' in data or 'etternamn' in data):
            if not data.get('namn'):
                raise ValidationError(
                    'Specify either fornamn+etternamn, or namn')
            namn = data['namn'].split()
            if len(namn) == 1:
                data['fornamn'] = namn.pop()
            else:
                data['etternamn'] = namn.pop()
                data['fornamn'] = ' '.join(namn)
        data.pop('namn', None)
        return data

    def create(self, validated_data):
        medlem = Medlem(**validated_data)
        lags = medlem.proposed_lokallag()
        medlem.lokallag = lags[0] if lags else None
        medlem.status = 'I'  # Infoperson
        medlem.innmeldingstype = 'H'  # Heimesida
        medlem.save()
        return medlem


class MedlemSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Medlem
        fields = ('url', 'fornamn', 'mellomnamn', 'etternamn',
                  'fodt', 'postadr', 'ekstraadr', 'postnr', 'epost', 'mobnr',
                  'borteadr', 'bortepostnr')
