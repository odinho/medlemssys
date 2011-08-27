# -*- coding: utf-8 -*-
# vim: ts=4 sts=4 expandtab ai

#from django.db import models
from django.contrib.admin.filters import RelatedFieldListFilter, DateFieldListFilter
from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext as _
from datetime import date

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
