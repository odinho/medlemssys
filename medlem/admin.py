# vim: ts=4 sts=4 expandtab ai
#from reversion.admin import VersionAdmin
from django.contrib import admin
from django.shortcuts import render_to_response
from django.http import HttpResponse
import csv
from models import *

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
    list_display = ('id', '__unicode__', 'lokallag', 'er_innmeldt',
                    'har_betalt', 'fodt_farga')
    list_display_links = ('id', '__unicode__')
    list_filter = ('lokallag',)
    save_on_top = True
    inlines = [RolleInline, GiroInline,]
    search_fields = ('fornamn', 'etternamn', '=pk',)
    filter_vertical = ('val',)
    fieldsets = (
        (None, {
            'classes': ('left',),
            'fields': (('fornamn', 'etternamn'),
                ('postadr', 'postnr', 'epost', 'mobnr'),
                'lokallag', 'fodt', 'innmeldt_dato',)
            }),
        (u'Ikkje pakravde felt', {
            'classes': ('left', 'collapse'),
            'fields': ('utmeldt_dato', 'val', 'nemnd', 'tilskiping', 'heimenr',)
        }),
    )
    actions = ['print_member_list',]

    class Media:
        css = {
            "all": ("/site_media/medlem.css",)
        }

    def print_member_list(self, request, queryset):
        liste = ""

        response = HttpResponse(mimetype="text/plain")
        dc = csv.DictWriter(response, queryset[0].__dict__)

        dc.writerow(list(queryset[0].__dict__))
        for m in queryset:
            dc.writerow(m.__dict__)

        return response

class MedlemInline(admin.TabularInline):
    model = Medlem
    extra = 3
    fields = ['fornamn', 'etternamn', 'postadr', 'postnr', 'epost', 'mobnr', 'fodt']

class LokallagAdmin(admin.ModelAdmin):
    inlines = [MedlemInline,]


admin.site.register(Medlem, MedlemAdmin)
admin.site.register(Lokallag, LokallagAdmin)
admin.site.register(Tilskiping)
admin.site.register(Rolletype)
admin.site.register(Nemnd)
admin.site.register(Val)
