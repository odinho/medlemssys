# -*- coding: utf-8 -*-
# vim: ts=4 sts=4 expandtab ai

#from django.db import models
from django.contrib.admin.filters import RelatedFieldListFilter, DateFieldListFilter, SimpleListFilter
from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext as _
from django.db.models import Q
from datetime import date

class SporjingFilter(SimpleListFilter):
    title = _(u"spørjingar")
    parameter_name = 'sporjing'

    def lookups(self, request, model_admin):
        return (
                ('teljande',    u"Teljande"),
                ('interessante',u"Interessante"),
                ('betalande',   u"Betalande"),
                ('potensielle', u"Potensielt teljande"),
            )

    def queryset(self, request, queryset):
        if self.value() == 'teljande':
            return queryset.model.objects.teljande()
        elif self.value() == 'interessante':
            return queryset.model.objects.interessante()
        elif self.value() == 'betalande':
            return queryset.model.objects.betalande()
        elif self.value() == 'potensielle':
            return queryset.model.objects.potensielt_teljande()


class FodtFilter(SimpleListFilter):
    parameter_name = "alder"
    title = _(u"alder i år")

    def lookups(self, request, model_admin):
        return (
                ('under-26',    u"Under 26 (teljande)"),
                ('over-25',     u"26 og eldre"),
                ('under-30',    u"Under 30"),
                ('over-29',     u"30 og eldre"),
                ('25',          u"25 år (sisteårs teljande)"),
                ('26',          u"26 år (ikkje teljande fyrste år)"),
                ('invalid',     u"Sære aldre"),
            )

    def queryset(self, request, queryset):
        year = date.today().year

        if self.value() == 'under-26':
            return queryset.filter(fodt__lt=(year - 26))
        elif self.value() == 'over-25':
            return queryset.filter(fodt__gt=(year - 25))
        if self.value() == 'under-30':
            return queryset.filter(fodt__lt=(year - 30))
        elif self.value() == 'over-29':
            return queryset.filter(fodt__gt=(year - 29))
        elif self.value() == '25':
            return queryset.filter(fodt=(year - 25))
        elif self.value() == '26':
            return queryset.filter(fodt=(year - 26))
        elif self.value() == 'invalid':
            return queryset.filter(Q(fodt__isnull=True) | Q(fodt__lt=(year-120)) | Q(fodt__gt=year))

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

    def used_params(self):
        return [self.lookup_kwarg_past_time, self.lookup_kwarg_isnull]


class AdditiveSubtractiveFilter(RelatedFieldListFilter):
    def __init__(self, field, request, params, model, model_admin, field_path):
        super(AdditiveSubtractiveFilter, self).__init__(
            field, request, params, model, model_admin, field_path)

        self.using_params = []
        self.paramstart = "adv_" + field.get_attname()
        # Setting this here, earlier it was done from within Django
        # it's now into several different variables
        if not hasattr(self, "params"):
            self.params = params

    def has_output(self):
        return len(self.lookup_choices) > 0

    def _make_param(self, field_id):
        return self.paramstart + str(field_id)

    def used_params(self):
        for lookup, title in self.lookup_choices:
            self.using_params.append(self._make_param(lookup))
        return self.using_params

    def queryset(self, request, queryset):
        for key, value in self.params.items():
            if value == 'e':
                queryset = queryset.exclude(val__id=key.replace(self.paramstart, ''))
            elif value == 'i':
                queryset = queryset.filter(val__id=key.replace(self.paramstart, ''))
        return queryset

    def choices(self, cl):
        yield {
            'selected': len(set(self.params).intersection(self.using_params)) == 0,
            'query_string': cl.get_query_string({}, self.using_params),
            'display': _('All'),
        }
        for p in (('i', _('Vis')), ('e', _('Skjul'))):
            for lookup, title in self.lookup_choices:
                yield {
                    'selected': p[0] == self.params.get(self._make_param(lookup)),
                    'query_string': cl.get_query_string({
                        self._make_param(lookup): p[0],
                    }, []),
                    'display': "%s '%s'" % (p[1], title),
                }
