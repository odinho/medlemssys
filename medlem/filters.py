# -*- coding: utf-8 -*-
# vim: ts=4 sts=4 expandtab ai

#from django.db import models
from django.contrib.admin.filterspecs import FilterSpec, DateFieldFilterSpec #, ChoicesFilterSpec
from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext as _
from datetime import date

class IsTimeSinceFilterSpec(DateFieldFilterSpec):
    """
    Adds filtering by future and previous values in the admin
    filter sidebar. Set the is_timesince_filter filter in the model field attribute
    'is_timesince_filter'.    my_model_field.is_timesince_filter = True
    """

    def __init__(self, f, request, params, model, model_admin, *args, **kwargs):
        super(IsTimeSinceFilterSpec, self).__init__(f, request, params, model,
                                                   model_admin, *args, **kwargs)
        one_year_ago = date(date.today().year - 1, 1, 1)
        two_years_ago = date(date.today().year - 2, 1, 1)
        self.links = (
            (_('All'), {}),
            (_(smart_unicode('Innan året')), {'%s__gte' % self.field.name: str(one_year_ago),
                       }),
            (_(smart_unicode('Innan fjoråret')), {'%s__gte' % self.field.name: str(two_years_ago),
                    }),
            (_('Aldri'), {'%s__isnull' % self.field.name: str(True),
                    }),
            (_('Har skjedd'), {'%s__isnull' % self.field.name: str(False),
                    }),

        )


    def title(self):
        return _("medlemspengar")

# registering the filter
FilterSpec.filter_specs.insert(0, (lambda f: getattr(f, 'is_timesince_filter', False),
                                   IsTimeSinceFilterSpec))
