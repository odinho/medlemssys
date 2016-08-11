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

from importlib import import_module

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


_cached_class = None

def get_behaviour():
    global _cached_class
    if _cached_class:
        return _cached_class
    mod_name = settings.BEHAVIOUR_MODULE
    mod = import_module(mod_name)
    try:
        _cached_class = getattr(mod, 'Behaviour')
    except AttributeError:
        raise ImproperlyConfigured(
            'Behaviour module "{0}" does not define a '
            '"Behaviour" class'.format(mod_name))
    return _cached_class
