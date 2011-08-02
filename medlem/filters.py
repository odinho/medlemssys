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


        past_year = date(date.today().year, 1, 1)
        past_two_years = date(date.today().year - 1, 1, 1)

        self.lookup_kwarg_past_time = '%s__gte' % self.field_path
        self.lookup_kwarg_isnull = '%s__isnull' % self.field_path

        self.links = (
            (_('All'), {}),
            (_(smart_unicode('Innan året')), {
                self.lookup_kwarg_past_time: str(past_year),
            }),
            (_(smart_unicode('Innan fjoråret')), {
                self.lookup_kwarg_past_time: str(past_two_years),
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
