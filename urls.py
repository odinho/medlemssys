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
    (r'^takk', 'django.views.generic.simple.direct_to_template',
        {'template': 'takk.html', }),
    (r'^stats/update/', 'medlemssys.statistikk.views.update'),
    (r'^stats/vervetopp/', 'medlemssys.statistikk.views.vervetopp'),
#    url(r'^newsletters/', include('emencia.django.newsletter.urls')),
    (r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': '/home/odin/Kode/medlemssys/static'}),
    )
