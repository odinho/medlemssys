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

from datetime import date

from django.contrib.admin.filters import DateFieldListFilter
from django.contrib.admin.filters import ListFilter
from django.contrib.admin.filters import RelatedFieldListFilter
from django.contrib.admin.filters import SimpleListFilter
from django.db.models import Q
from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext as _

from medlemssys.behaviour import get_behaviour

from .models import PostNummer


class CustomFilter(SimpleListFilter):
    behaviour_variable = None

    def __init__(self, *args, **kwargs):
        self.filters = getattr(get_behaviour(), self.behaviour_variable)
        return super(CustomFilter, self).__init__(*args, **kwargs)

    def lookups(self, request, model_admin):
        return [(v.key, v.title) for v in self.filters]

    def queryset(self, request, queryset):
       lookup = next((v for v in self.filters if v.key == self.value()), None)
       if lookup:
           return lookup.filter(queryset)


class SporjingFilter(CustomFilter):
    title = _(u"spørjingar")
    parameter_name = 'sporjing'
    behaviour_variable = 'medlem_ui_filters'


class GiroSporjingFilter(CustomFilter):
    title = _(u"giro-spørjingar")
    parameter_name = 'sporjing'
    behaviour_variable = 'giro_ui_filters'


class StadFilter(ListFilter):
    title = _(u"stad")

    def __init__(self, request, params, model, model_admin):
        super(StadFilter, self).__init__(
            request, params, model, model_admin)
        self.request = request
        for p in self.expected_parameters():
            if p in params:
                value = params.pop(p)
                self.used_parameters[p] = value

    def param(self, var):
        return self.used_parameters.get(var, None)

    def has_output(self):
        return True

    def expected_parameters(self):
        return ('stad_fylke', 'stad_kommune')

    def choices(self, cl):
        qs = cl.get_queryset(self.request)
        yield {
            'selected': self.param('stad_fylke') is None,
            'query_string': cl.get_query_string(
                {}, ['stad_fylke', 'stad_kommune']),
            'display': _('All'),
        }
        if self.param('stad_fylke') is None:
            if qs.count() < 1000:
                # Converting the QuerySet __in to a list because of a MySQL
                # performance issue
                fylke_qs = PostNummer.objects.filter(
                    postnr__in=list(qs.values('postnr')))
            else:
                fylke_qs = PostNummer.objects.all()
            for fylke in fylke_qs.values_list('fylke', flat=True).distinct():
                yield {
                    'selected': self.param('stad_fylke') == fylke,
                    'query_string': cl.get_query_string({
                        'stad_fylke': fylke,
                    }, []),
                    'display': fylke,
                }
        else:
            fylke = self.param('stad_fylke')
            yield {
                'selected': True,
                'query_string': cl.get_query_string({
                    'stad_fylke': fylke,
                }, ['stad_kommune']),
                'display': fylke,
            }
            # Kommunar som er i dette fylket

            # Converting the QuerySet __in to a list because of a MySQL
            # performance issue
            kommune_qs = (
                PostNummer.objects.filter(
                    postnr__in=list(qs.values_list('postnr', flat=True)),
                    fylke=fylke)
                .values_list('kommune', flat=True)
                .distinct())
            for kommune in kommune_qs:
                yield {
                    'selected': self.param('stad_kommune') == kommune,
                    'query_string': cl.get_query_string({
                        'stad_kommune': kommune,
                    }, []),
                    'display': u'– {0}'.format(smart_unicode(kommune)),
                }

    def queryset(self, request, queryset):
        if self.param('stad_kommune'):
            return queryset.kommune(
                       self.param('stad_kommune'),
                       fylke=self.param('stad_fylke'))
        elif self.param('stad_fylke'):
            return queryset.fylke(self.param('stad_fylke'))
        return queryset


class FodtFilter(SimpleListFilter):
    title = _(u"alder i år")
    parameter_name = "alder"
    field = 'fodt'

    def lookups(self, request, model_admin):
        return (
                ('under-26', u"Under 26 (teljande)"),
                ('over-25',  u"26 og eldre"),
                ('under-30', u"Under 30"),
                ('over-29',  u"30 og eldre"),
                ('25',       u"25 år (sisteårs teljande)"),
                ('26',       u"26 år (ikkje teljande fyrste år)"),
                ('invalid',  u"Sære aldre"),
            )

    def queryset(self, request, queryset):
        year = date.today().year

        restriction = {}
        if self.value() == 'under-26':
            restriction = { self.field + '__gt': (year - 26)}
        elif self.value() == 'over-25':
            restriction = { self.field + '__lt': (year - 25)}
        if self.value() == 'under-30':
            restriction = { self.field + '__gt': (year - 30)}
        elif self.value() == 'over-29':
            restriction = { self.field + '__lt': (year - 29)}
        elif self.value() == '25':
            restriction = { self.field: (year - 25)}
        elif self.value() == '26':
            restriction = { self.field: (year - 26)}
        elif self.value() == 'invalid':
            return queryset.filter(Q(**{self.field + '__isnull': True}) |
                                   Q(**{self.field + '__lt': (year-120)}) |
                                   Q(**{self.field + '__gt': year}))
        return queryset.filter(**restriction)


class MedlemFodtFilter(FodtFilter):
    field = 'medlem__fodt'


class TimeSinceFilter(DateFieldListFilter):
    def __init__(self, field, request, params, model, model_admin, field_path):
        super(TimeSinceFilter, self).__init__(field, request, params,
                model, model_admin, field_path)

        this_year = date(date.today().year, 1, 1)
        last_year = date(date.today().year - 1, 1, 1)

        self.lookup_kwarg_past_time = '%s__gte' % self.field_path
        self.lookup_kwarg_lt_time = '%s__lt' % self.field_path
        self.lookup_kwarg_isnull = '%s__isnull' % self.field_path

        self.links = (
            (_('All'), {}),
            (_(smart_unicode('Innan året')), {
                self.lookup_kwarg_past_time: str(this_year),
            }),
            (_(smart_unicode('Innan fjoråret')), {
                self.lookup_kwarg_past_time: str(last_year),
            }),
            (_(smart_unicode('I fjor')), {
                self.lookup_kwarg_past_time: str(last_year),
                self.lookup_kwarg_lt_time: str(this_year),
            }),
            (_(smart_unicode('I fjor eller eldre')), {
                self.lookup_kwarg_lt_time: str(this_year),
            }),
            (_('Aldri'), {
                self.lookup_kwarg_isnull: str(True),
            }),
            (_('Har skjedd'), {
                self.lookup_kwarg_isnull: str(False),
            }),
        )


class AdditiveSubtractiveFilter(RelatedFieldListFilter):
    def __init__(self, field, request, params, model, model_admin, field_path):
        self.using_params = []
        self.paramstart = "adv_" + field.get_attname()

        super(AdditiveSubtractiveFilter, self).__init__(
            field, request, params, model, model_admin, field_path)

    def has_output(self):
        return len(self.lookup_choices) > 0

    def _make_param(self, field_id):
        return self.paramstart + str(field_id)

    def expected_parameters(self):
        for lookup, title in self.lookup_choices:
            self.using_params.append(self._make_param(lookup))
        return self.using_params

    def queryset(self, request, queryset):
        for key, value in self.used_parameters.items():
            if value == 'exc':
                queryset = queryset.exclude(
                    val__id=key.replace(self.paramstart, ''))
            elif value == 'inc':
                queryset = queryset.filter(
                    val__id=key.replace(self.paramstart, ''))
        return queryset

    def choices(self, cl):
        used_params = set(self.used_parameters).intersection(self.using_params)
        yield {
            'selected': len(used_params) == 0,
            'query_string': cl.get_query_string({}, self.using_params),
            'display': _("All"),
        }
        for p in (('inc', _("Vis")), ('exc', _("Skjul"))):
            for lookup, title in self.lookup_choices:
                # If the link is selected
                if p[0] == self.used_parameters.get(self._make_param(lookup)):
                    yield {
                        'selected': True,
                        'query_string': cl.get_query_string({},
                            [ self._make_param(lookup) ]),
                        'display': "%s '%s'" % (p[1], title),
                    }
                else:
                    yield {
                        'selected': False,
                        'query_string': cl.get_query_string({
                            self._make_param(lookup): p[0],
                        }, []),
                        'display': "%s '%s'" % (p[1], title),
                    }
