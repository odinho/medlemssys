# vim: ts=4 sts=4 expandtab ai
from django.contrib import admin
from models import *

class LokallagsmedlemskapInline(admin.TabularInline):
    model = Lokallagsmedlemskap
    extra = 1
class GiroInline(admin.TabularInline):
    model = Giro
    extra = 1
    classes = ['left']
    fields = ['belop', 'kid', 'oppretta', 'innbetalt', 'desc']
class RolleInline(admin.TabularInline):
    model = Rolle
    extra = 1
    classes = ['left']

class MedlemAdmin(admin.ModelAdmin):
    model_admin_manager = Medlem.objects
    list_display = ('id', '__unicode__', 'get_lokallag', 'er_innmeldt',
                    'har_betalt', 'fodt_farga')
    list_display_links = ('id', '__unicode__')
    list_filter = ('lokallag_denorm',)
    save_on_top = True
    inlines = [LokallagsmedlemskapInline, RolleInline, GiroInline,]
    search_fields = ('fornamn', 'etternamn', '=pk',)
    filter_vertical = ('val',)
    fieldsets = (
        (None, {
            'classes': ('left',),
            'fields': (('fornamn', 'etternamn'),
                ('postadr', 'postnr', 'epost', 'mobnr'),
                'fodt', 'innmeldt_dato',)
            }),
        (u'Ikkje pakravde felt', {
            'classes': ('left', 'collapse'),
            'fields': ('utmeldt_dato', 'val', 'nemnd', 'tilskiping', 'heimenr',)
        }),
    )

    class Media:
        css = {
            "all": ("/site_media/medlem.css",)
        }

    class LokallagAdmin():
        pass

admin.site.register(Medlem, MedlemAdmin)
admin.site.register(Tilskiping)
admin.site.register(Rolletype)
admin.site.register(Lokallag)
admin.site.register(Nemnd)
admin.site.register(Val)
