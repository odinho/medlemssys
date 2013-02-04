# -*- coding: utf-8 -*-
# vim: ts=4 sts=4 expandtab ai
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from reversion.admin import VersionAdmin

from medlemssys.settings import STATIC_URL
from filters import AdditiveSubtractiveFilter, FodtFilter, SporjingFilter #, Filter, TimeSince

import admin_actions
from models import *

class GiroInline(admin.TabularInline):
    model = Giro
    extra = 1
    classes = ['left']
    fields = ['belop', 'innbetalt_belop', 'kid', 'gjeldande_aar', 'innbetalt', 'konto', 'desc', 'status']
    readonly_fields = ('status',)
class RolleInline(admin.TabularInline):
    model = Rolle
    extra = 1
    classes = ['left']
class VervaMedlemInline(admin.TabularInline):
    model = Medlem
    fk_name = 'verva_av'
    verbose_name = _("verving")
    verbose_name_plural = _("vervingar")
    extra = 0
    classes = ['left']
    fields = ['innmeldingstype', 'innmeldingsdetalj', 'lokallag', 'innmeldt_dato', '_siste_medlemspengar', 'fodt_farga', 'er_innmeldt', 'har_betalt']
    readonly_fields = ('innmeldingstype', 'innmeldt_dato', '_siste_medlemspengar', 'fodt_farga', 'er_innmeldt', 'har_betalt')

class MedlemAdmin(VersionAdmin):
    list_display = ('id', '__unicode__', 'lokallag_changelist', 'er_innmeldt',
                    'har_betalt', 'fodt_farga', 'status_html')
    list_display_links = ('id', '__unicode__')
    date_hierarchy = 'innmeldt_dato'
    list_filter = (
            SporjingFilter,
            ('val', AdditiveSubtractiveFilter),
            #('_siste_medlemspengar', TimeSinceFilter),
            '_siste_medlemspengar',
            FodtFilter,
            'innmeldt_dato',
            'utmeldt_dato',
            'status',
            'lokallag',
            'giroar__status',
        )
    raw_id_fields = ['verva_av', 'betalt_av']
    readonly_fields = ('_siste_medlemspengar', 'oppretta', 'oppdatert')
    save_on_top = True
    inlines = [RolleInline, GiroInline, VervaMedlemInline]
    search_fields = ('fornamn', 'mellomnamn', 'etternamn', '=id', '^mobnr',)
    filter_horizontal = ('val', 'tilskiping')
    fieldsets = (
        (None, {
            'classes': ('left',),
            'fields': (
                ('fornamn', 'mellomnamn', 'etternamn', 'fodt', 'kjon'),
                ('postadr', 'postnr', 'ekstraadr'),
                ('mobnr', 'epost'),
                ('lokallag', 'status', 'innmeldt_dato'),
            )
            }),
        (u'Ikkje pakravde felt', {
            'classes': ('left', 'collapse'),
            'fields': (
                ('utmeldt_dato', '_siste_medlemspengar', 'user'),
                ('heimenr', 'gjer'),
                ('innmeldingstype', 'innmeldingsdetalj', 'verva_av'),
                'merknad',
                ('borteadr', 'bortepostnr', 'betalt_av'),
                ('val', 'tilskiping', 'nemnd'),
                ('oppretta', 'oppdatert'),
            )
        }),
    )
    actions = [ admin_actions.simple_member_list,
                admin_actions.csv_member_list,
                admin_actions.pdf_giro,
                admin_actions.lag_giroar, ]

    class Media:
        css = {
            "all": (STATIC_URL + "medlem.css",
                STATIC_URL + "css/forms.css",)
        }

    def queryset(self, request):
        self._get_params = request.GET

        # use our manager, rather than the default one
        qs = self.model.objects.alle()

        # we need this from the superclass method
        ordering = self.ordering or () # otherwise we might try to *None, which is bad ;)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

    def lokallag_changelist(self, obj):
        url = reverse('admin:medlem_medlem_changelist')
        querystring = self._get_params.copy()
        querystring['lokallag__id__exact'] = obj.lokallag.pk
        return u'<a href="{0}?{1}">{2}</a>'.format(url,
                                                   querystring.urlencode(),
                                                   obj.lokallag)
    lokallag_changelist.short_description = _("Lokallag")
    lokallag_changelist.admin_order_field = 'lokallag__name'
    lokallag_changelist.allow_tags = True


class MedlemInline(admin.TabularInline):
    model = Medlem
    extra = 3
    fields = ['fornamn', 'etternamn', 'postadr', 'postnr', 'epost', 'mobnr', 'fodt']

class LokallagAdmin(admin.ModelAdmin):
    list_display = ('pk', 'namn', 'num_medlem', 'andsvar',
                    'fylkeslag', 'distrikt', 'lokalsats', 'aktivt')
    list_editable = ('namn', 'andsvar', 'lokalsats', 'aktivt')
    list_per_page = 200
    inlines = [MedlemInline,]
    prepopulated_fields = {"slug": ("namn",)}


class TilskipInline(admin.TabularInline):
    model = Medlem.tilskiping.through
    raw_id_fields = ['medlem']
class TilskipAdmin(admin.ModelAdmin):
    model = Tilskiping
    list_display = ('__unicode__', 'slug', 'start', 'stopp', 'num_deltakarar')
    inlines = [TilskipInline,]


class NemndInline(admin.TabularInline):
    model = Medlem.nemnd.through
    raw_id_fields = ['medlem']
class NemndAdmin(admin.ModelAdmin):
    list_display = ('pk', 'namn', 'start', 'stopp',)
    list_editable = ('namn',)
    inlines = [NemndInline,]

class ValInline(admin.TabularInline):
    model = Medlem.val.through
    raw_id_fields = ['medlem']
class ValAdmin(admin.ModelAdmin):
    model = Val
    inlines = [ValInline,]

class GiroAdmin(admin.ModelAdmin):
    model = Giro
    raw_id_fields = ['medlem']
    list_display = ('pk', 'medlem_admin_change', 'kid', 'belop', 'innbetalt_belop', 'gjeldande_aar', 'innbetalt', 'konto', 'status')
    list_editable = ('innbetalt', 'innbetalt_belop', 'gjeldande_aar', 'status', )
    date_hierarchy = 'oppretta'
    list_filter = (
        'status',
        'gjeldande_aar',
        'innbetalt',
        'hensikt',
        'konto',
        'belop',
    )
    readonly_fields = ('oppretta',)
    fieldsets = (
        (None, {
            'fields': (
                'medlem',
                ('belop', 'innbetalt_belop'),
                ('konto', 'hensikt'),
                'innbetalt',
                'kid',
                ('gjeldande_aar', 'oppretta', 'status'),
                'desc',
            )
        }),
    )

    def medlem_admin_change(self, obj):
        url = reverse('admin:medlem_medlem_change', args=(obj.medlem_id,))
        return u'<a href="{0}">{1}</a>'.format(url, obj.medlem)
    medlem_admin_change.short_description = _("Medlem")
    medlem_admin_change.admin_order_field = 'medlem'
    medlem_admin_change.allow_tags = True


# XXX: Dette fungerer i Django 1.2
#class NemndmedlemskapInline(MedlemInline):
#    model = Medlem.nemnd.through
#class NemndAdmin(admin.ModelAdmin):
#    inlines = [NemndmedlemskapInline,]
#admin.site.register(Nemnd, NemndAdmin)

admin.site.register(Medlem, MedlemAdmin)
admin.site.register(Lokallag, LokallagAdmin)
admin.site.register(Tilskiping, TilskipAdmin)
admin.site.register(Nemnd, NemndAdmin)
admin.site.register(Giro, GiroAdmin)

admin.site.register(LokallagOvervaking)
admin.site.register(Rolletype)
admin.site.register(PostNummer)

# Ta med lokallag ekstra (XXX: Usikkert om eg treng rolletype og giro)
#reversion.register(Medlem, follow=["rolle_set", "giroar", "lokallag"])
#reversion.register(Lokallag)
