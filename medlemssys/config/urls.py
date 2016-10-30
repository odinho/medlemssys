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
from __future__ import unicode_literals

import django.contrib.auth.views
from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic import TemplateView
from django.views import defaults as default_views

import medlemssys.api.urls as api_urls
import medlemssys.giro.admin_views as giro_admin
import medlemssys.innhenting.views as innhenting
import medlemssys.medlem.lokallag as lokallag
import medlemssys.medlem.views as medlem
import medlemssys.statistikk.admin_views as statistikk_admin
import medlemssys.statistikk.views as statistikk


urlpatterns = [
    url(r'^$',
        TemplateView.as_view(template_name='pages/home.html'), name='home'),
    url(r'^robots.txt$',
        TemplateView.as_view(template_name='pages/robots.txt'), name='robots'),

    url(r'^admin/innhenting/import_ocr/',
        innhenting.import_ocr, name='import_ocr'),
    url(r'^admin/medlem/giro/send/', giro_admin.send, name='giro_send'),
    url(r'^admin/medlem/giro/manual/',
        giro_admin.manual_girosearch, name='giro_manual'),
    url(r'^admin/revisions/',
        statistikk_admin.show_revisions, name='show_revisions'),
    # Django Admin, use {% url 'admin:index' %}
    url(settings.ADMIN_URL, include(admin.site.urls)),

    url(r'^accounts/login/$',
        django.contrib.auth.views.login, { 'template_name': 'login.html' }),
    url(r'^accounts/logout/$',
        django.contrib.auth.views.logout, { 'next_page': '/' }),
    url(r'^medlem/opprett', medlem.create_medlem),
    url(r'^medlem/(?P<id>\d+)/endra/(?P<nykel>\w+)',
        medlem.edit_medlem, name='medlem_edit'),
    url(r'^medlem/ringjelister', medlem.ringjelister),
    url(r'^lokallag/$', lokallag.home),
    url(r'^lokallag/(?P<slug>[-\w]+)/$',
        lokallag.lokallag_home, name='lokallag_home'),
    url(r'^takk', TemplateView.as_view(template_name='takk.html')),
    url(r'^stats/vervetopp/', statistikk.vervetopp),
    url(r'^stats/vervometer/', statistikk.vervometer),
    url(r'^member/search/', medlem.search, name='search'),
    url(r'^api/get_members.json',
        medlem.get_members_json, name='get_members_json'),
    url(r'^api/', include(api_urls), name='api-root'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        url(r'^400/$', default_views.bad_request,
            kwargs={'exception': Exception('Bad Request!')}),
        url(r'^403/$', default_views.permission_denied,
            kwargs={'exception': Exception('Permission Denied')}),
        url(r'^404/$', default_views.page_not_found,
            kwargs={'exception': Exception('Page not Found')}),
        url(r'^500/$', default_views.server_error),
    ]
