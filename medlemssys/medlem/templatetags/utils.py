# -*- coding: utf-8 -*-
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
from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
@stringfilter
def split(str,splitter=","):
    return str.split(splitter)

@register.simple_tag
def val_option(medlem, val, not_val):
    selected = ''
    if (all(medlem.val_exists(v) for v in val.split(',')) and
            not any(medlem.val_exists(v) for v in not_val.split(','))):
        selected='selected'
    return u'<option {sel} value="{value}">'.format(sel=selected, value=val)

@register.simple_tag
def val_checked(medlem, val):
    if medlem.val_exists(val):
        return 'checked'
    return ''

@register.simple_tag
def val_exists(medlem, val):
    if medlem.val_exists(val):
        return val
    return ''
