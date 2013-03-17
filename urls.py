from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    (r'^accounts/login/$', 'django.contrib.auth.views.login', { 'template_name': 'login.html' }),
    (r'^accounts/logout/$', 'django.contrib.auth.views.logout', { 'next_page': '/' }),
    (r'^medlem/add', 'medlemssys.medlem.views.create_medlem'),
    (r'^medlem/ringjelister', 'medlemssys.medlem.views.ringjelister'),
    (r'^lokallag/$',
        'medlemssys.medlem.lokallag.home'),
    (r'^lokallag/(?P<slug>[-\w]+)/$',
        'medlemssys.medlem.lokallag.lokallag_home'),
    (r'^tilskiping/$',
        'medlemssys.medlem.tilskiping.listing'),
    (r'^tilskiping/(?P<slug>[-\w]+)/$',
        'medlemssys.medlem.tilskiping.detail'),
    (r'^takk', 'django.views.generic.simple.direct_to_template',
        {'template': 'takk.html', }),
    (r'^stats/vervetopp/', 'medlemssys.statistikk.views.vervetopp'),
    (r'^stats/vervometer/', 'medlemssys.statistikk.views.vervometer'),
#    url(r'^newsletters/', include('emencia.django.newsletter.urls')),
    url(r'^admin/innhenting/import_ocr/', 'medlemssys.innhenting.views.import_ocr', name='import_ocr'),
    (r'^admin/', include(admin.site.urls)),
    url(r'^api/get_members.json', 'medlemssys.medlem.views.get_members_json', name='get_members_json'),
    url(r'^member/search/', 'medlemssys.medlem.views.search', name='search'),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': '/home/odin/Kode/medlemssys/static'}),
    )
