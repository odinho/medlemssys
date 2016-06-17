# -*- coding: utf-8 -*-
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
import django.views.static
from django.conf import settings
from django.conf.urls import include
from django.conf.urls import url
from django.contrib import admin
from django.views.generic.base import TemplateView

import giro.admin_views
import innhenting.views
import medlem.lokallag
import medlem.views
import statistikk.admin_views
import statistikk.views


admin.autodiscover()

urlpatterns = [
]

if settings.DEBUG:
    urlpatterns += [
        url(r'^static/(?P<path>.*)$', django.views.static.serve,
            {'document_root': '/home/odin/Kode/medlemssys/static'}),
    ]
