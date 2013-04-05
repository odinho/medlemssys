# -*- coding: utf-8 -*-
# vim: ts=4 sts=4 expandtab ai
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from reversion_compare.admin import CompareVersionAdmin

from medlemssys.settings import STATIC_URL
from filters import AdditiveSubtractiveFilter, FodtFilter, MedlemFodtFilter,SporjingFilter, GiroSporjingFilter #, Filter, TimeSince

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

class MedlemAdmin(CompareVersionAdmin):
    list_display = ('id', '__unicode__', 'lokallag_changelist', 'er_innmeldt',
                    'siste_giro_info', 'fodt_farga', 'status_html')
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
            'tilskiping',
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
                ('utmeldt_dato', '_siste_medlemspengar', 'user', 'nykel'),
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
                admin_actions.csv_list,
                admin_actions.lag_giroar, ]

    class Media:
        css = {
            "all": (STATIC_URL + "medlem.css",
                STATIC_URL + "css/forms.css",)
        }

    def get_actions(self, request):
        """Puts the delete action on the bottom"""
        actions = super(MedlemAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            deleteaction = actions['delete_selected']
            del actions['delete_selected']
            actions['delete_selected'] = deleteaction
        return actions


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

    def siste_giro_info(self, obj):
        gjeldande = obj.gjeldande_giro()
        if gjeldande:
            return gjeldande.admin_change()
        fjor = obj.gjeldande_giro(datetime.today().year - 1)
        if fjor:
            return '{0}: {1}'.format(fjor.gjeldande_aar, fjor.admin_change())
        return '&mdash;'
    siste_giro_info.short_description = _("Siste giro")
    siste_giro_info.admin_order_field = 'giroar'
    siste_giro_info.allow_tags = True

class MedlemInline(admin.TabularInline):
    model = Medlem
    extra = 3
    fields = ['fornamn', 'etternamn', 'postadr', 'postnr', 'epost', 'mobnr', 'fodt']

class LokallagAdmin(CompareVersionAdmin):
    list_display = ('pk', 'namn', 'num_medlem', 'andsvar',
                    'fylkeslag', 'distrikt', 'lokalsats', 'aktivt')
    list_editable = ('namn', 'andsvar', 'lokalsats', 'aktivt')
    list_per_page = 200
    inlines = [MedlemInline,]
    prepopulated_fields = {"slug": ("namn",)}

class LokallagOvervakingAdmin(CompareVersionAdmin):
    model = LokallagOvervaking
    raw_id_fields = ['medlem']

class TilskipInline(admin.TabularInline):
    model = Medlem.tilskiping.through
    raw_id_fields = ['medlem']
class TilskipAdmin(CompareVersionAdmin):
    model = Tilskiping
    list_display = ('__unicode__', 'slug', 'start', 'stopp', 'num_deltakarar')
    inlines = [TilskipInline,]


class NemndInline(admin.TabularInline):
    model = Medlem.nemnd.through
    raw_id_fields = ['medlem']
class NemndAdmin(CompareVersionAdmin):
    list_display = ('pk', 'namn', 'start', 'stopp',)
    list_editable = ('namn',)
    inlines = [NemndInline,]

class ValInline(admin.TabularInline):
    model = Medlem.val.through
    raw_id_fields = ['medlem']
class ValAdmin(CompareVersionAdmin):
    model = Val
    inlines = [ValInline,]
    fieldsets = (
        (None, {
            'fields': ('tittel', 'forklaring'),
            'description': 'Val er avslått som standard, so det er lurt å utforma '
                           'vala slik at dei fleste ikkje treng ha dei på. T.d. '
                           '«Ikkje ring» i staden for «Ring».',
        }),
    )

class GiroAdmin(CompareVersionAdmin):
    model = Giro
    raw_id_fields = ['medlem']
    list_display = ('pk', 'medlem_admin_change', 'kid', 'belop', 'innbetalt_belop', 'gjeldande_aar', 'innbetalt', 'konto', 'status')
    list_editable = ('innbetalt', 'innbetalt_belop', 'gjeldande_aar', 'status', )
    date_hierarchy = 'oppretta'
    list_filter = (
        'status',
        GiroSporjingFilter,
        'gjeldande_aar',
        'innbetalt',
        'hensikt',
        'konto',
        'belop',
        MedlemFodtFilter,
        'medlem__lokallag',
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
    actions = [
                admin_actions.giro_status_ferdig,
                admin_actions.giro_status_postlagt,
                admin_actions.giro_list,
                admin_actions.csv_list,
                admin_actions.pdf_giro,
            ]
    def medlem_admin_change(self, obj):
        return obj.medlem.admin_change()
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
admin.site.register(Val, ValAdmin)
admin.site.register(Nemnd, NemndAdmin)
admin.site.register(Giro, GiroAdmin)
admin.site.register(LokallagOvervaking, LokallagOvervakingAdmin)

admin.site.register(Rolletype)
admin.site.register(PostNummer)

# Ta med lokallag ekstra (XXX: Usikkert om eg treng rolletype og giro)
#reversion.register(Medlem, follow=["rolle_set", "giroar", "lokallag"])
#reversion.register(Lokallag)
