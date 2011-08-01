from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    (r'^medlem/add', 'medlemssys.medlem.views.create_medlem'),
    (r'^takk', 'django.views.generic.simple.direct_to_template',
        {'template': 'takk.html', }),
    (r'^import/', 'medlemssys.innhenting.views.fraa_nmu_csv'),
#    url(r'^newsletters/', include('emencia.django.newsletter.urls')),
    (r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': '/home/odin/Kode/medlemssys/static'}),
    )
