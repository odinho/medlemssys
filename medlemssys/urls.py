from django.conf.urls import patterns, url, include
from django.conf import settings
from django.contrib import admin
from django.views.generic.base import TemplateView

admin.autodiscover()

urlpatterns = patterns('',
    (r'^accounts/login/$', 'django.contrib.auth.views.login', { 'template_name': 'login.html' }),
    (r'^accounts/logout/$', 'django.contrib.auth.views.logout', { 'next_page': '/' }),
    (r'^medlem/opprett', 'medlem.views.create_medlem'),
    url(r'^medlem/(?P<id>\d+)/endra/(?P<nykel>\w+)', 'medlem.views.edit_medlem', name='medlem_edit'),
    (r'^medlem/ringjelister', 'medlem.views.ringjelister'),
    (r'^lokallag/$',
        'medlem.lokallag.home'),
    url(r'^lokallag/(?P<slug>[-\w]+)/$',
        'medlem.lokallag.lokallag_home', name='lokallag_home'),
    (r'^takk', TemplateView.as_view(template_name='takk.html')),
    (r'^stats/vervetopp/', 'statistikk.views.vervetopp'),
    (r'^stats/vervometer/', 'statistikk.views.vervometer'),
#    url(r'^newsletters/', include('emencia.django.newsletter.urls')),
    url(r'^admin/innhenting/import_ocr/', 'innhenting.views.import_ocr', name='import_ocr'),
    url(r'^admin/medlem/giro/send/', 'giro.admin_views.send', name='giro_send'),
    url(r'^admin/medlem/giro/manual/', 'giro.admin_views.manual_girosearch', name='giro_manual'),
    url(r'^admin/revisions/', 'statistikk.admin_views.show_revisions', name='show_revisions'),
    (r'^admin/', include(admin.site.urls)),
    url(r'^api/get_members.json', 'medlem.views.get_members_json', name='get_members_json'),
    url(r'^member/search/', 'medlem.views.search', name='search'),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': '/home/odin/Kode/medlemssys/static'}),
    )
