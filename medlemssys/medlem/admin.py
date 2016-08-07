# -*- coding: utf-8 -*-
# vim: ts=4 sts=4 expandtab ai

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
import datetime

from django.contrib import admin
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from reversion_compare.admin import CompareVersionAdmin

from . import admin_actions
from . import filters
from . import models


class GiroInline(admin.TabularInline):
    model = models.Giro
    extra = 1
    classes = ['left']
    fields = ['belop', 'innbetalt_belop', 'kid', 'gjeldande_aar', 'innbetalt', 'konto', 'desc', 'status']
    readonly_fields = ('status',)
class RolleInline(admin.TabularInline):
    model = models.Rolle
    extra = 1
    classes = ['left']
class VervaMedlemInline(admin.TabularInline):
    model = models.Medlem
    fk_name = 'verva_av'
    verbose_name = _("verving")
    verbose_name_plural = _("vervingar")
    extra = 0
    classes = ['left']
    fields = [
        'admin_change', 'innmeldingstype', 'innmeldingsdetalj',
        'lokallag', 'postnr', 'innmeldt_dato', '_siste_medlemspengar',
        'fodt_farga', 'er_innmeldt', 'har_betalt']
    readonly_fields = (
        'innmeldingstype', 'admin_change', 'postnr', 'innmeldt_dato',
        '_siste_medlemspengar', 'fodt_farga', 'er_innmeldt', 'har_betalt')


class MedlemAdmin(CompareVersionAdmin):
    list_display = ('id', '__unicode__', 'lokallag_changelist', 'er_innmeldt',
                    'siste_giro_info', 'fodt_farga', 'status_html')
    list_display_links = ('id', '__unicode__')
    date_hierarchy = 'innmeldt_dato'
    list_filter = (
            filters.SporjingFilter,
            ('val', filters.AdditiveSubtractiveFilter),
            #('_siste_medlemspengar', TimeSinceFilter),
            filters.FodtFilter,
            filters.StadFilter,
            '_siste_medlemspengar',
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
    filter_horizontal = ('val',)
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
                ('val',),
                ('oppretta', 'oppdatert'),
            )
        }),
    )
    actions = [ admin_actions.simple_member_list,
                admin_actions.csv_list,
                admin_actions.lag_giroar,
                admin_actions.suggest_lokallag,
                admin_actions.members_meld_ut,
              ]

    def get_actions(self, request):
        """Puts the delete action on the bottom"""
        actions = super(MedlemAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            deleteaction = actions['delete_selected']
            del actions['delete_selected']
            actions['delete_selected'] = deleteaction
        return actions


    def get_queryset(self, request):
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
        if not obj.lokallag:
            querystring['lokallag__isnull'] = True
        else:
            querystring['lokallag__id__exact'] = obj.lokallag.pk
        return u'<a href="{0}?{1}">{2}</a>'.format(url,
                                                   querystring.urlencode(),
                                                   obj.lokallag_display())
    lokallag_changelist.short_description = _("Lokallag")
    lokallag_changelist.admin_order_field = 'lokallag__namn'
    lokallag_changelist.allow_tags = True

    def siste_giro_info(self, obj):
        gjeldande = obj.gjeldande_giro()
        if gjeldande:
            return gjeldande.admin_change()
        fjor = obj.gjeldande_giro(datetime.date.today().year - 1)
        if fjor:
            return '{0}: {1}'.format(fjor.gjeldande_aar, fjor.admin_change())
        return '&mdash;'
    siste_giro_info.short_description = _("Siste giro")
    siste_giro_info.admin_order_field = 'giroar'
    siste_giro_info.allow_tags = True


class RolleInline(admin.TabularInline):
    model = models.Rolle
    extra = 0
    raw_id_fields = ['medlem']


class LokallagAdmin(CompareVersionAdmin):
    list_display = ('pk', 'namn_med_stad', 'num_medlem', 'andsvar',
                    'epost', 'aktivt', 'styret_admin', 'overvakingar')
    list_editable = ('andsvar', 'aktivt',)
    list_per_page = 200
    list_filter = (
        'aktivt',
        'rolle_set__rolletype',
        'lokalsats',
    )
    inlines = [RolleInline,]
    prepopulated_fields = {'slug': ('namn',)}

    def overvakingar(self, obj):
        def html(o):
            return u'<a href="{url}" title="Til: {epostar}">{tekst}</a>'.format(
                url=reverse('admin:medlem_lokallagovervaking_change',
                            args=(o.pk,)),
                epostar=o.epostar_admin(), tekst=unicode(o))
        return u', '.join(html(o) for o in obj.lokallag_overvaking_set.all())
    overvakingar.allow_tags = True

    def namn_med_stad(self, obj):
        return u'<span title="kommunar: {}\nfylke: {}">{}</span>'.format(
            obj.kommunes, obj.fylke, obj.namn)
    namn_med_stad.allow_tags = True
    namn_med_stad.admin_order_field = 'namn'


class LokallagOvervakingAdmin(CompareVersionAdmin):
    date_hierarchy = 'sist_oppdatert'
    model = models.LokallagOvervaking
    list_display = ('__unicode__', 'lokallag', 'medlem', 'epost',
                    'styreepostar', 'sist_oppdatert')
    list_per_page = 250
    list_filter = ('deaktivert', 'lokallag__aktivt')
    fields = ('medlem', 'epost', 'lokallag', 'deaktivert', 'sist_oppdatert',
              'epostar_admin')
    readonly_fields = ('sist_oppdatert', 'epostar_admin',)
    raw_id_fields = ['medlem']

    def styreepostar(self, obj):
        return ', '.join(obj.lokallag.styreepostar())


class ValInline(admin.TabularInline):
    model = models.Medlem.val.through
    raw_id_fields = ['medlem']
class ValAdmin(CompareVersionAdmin):
    list_display = ('tittel', 'forklaring', 'num_medlem')
    model = models.Val
    inlines = [ValInline,]
    fieldsets = (
        (None, {
            'fields': ('tittel', 'forklaring'),
            'description': "Val er avslått som standard, so det er lurt å utforma "
                           "vala slik at dei fleste ikkje treng ha dei på. T.d. "
                           "«Ikkje ring» i staden for «Ring».",
        }),
    )


class GiroAdmin(CompareVersionAdmin):
    model = models.Giro
    raw_id_fields = ['medlem']
    list_display = ('pk', 'medlem_admin_change', 'kid', 'belop',
                    'innbetalt_belop', 'gjeldande_aar', 'innbetalt', 'konto',
                    'status')
    list_editable = ('innbetalt', 'innbetalt_belop', 'gjeldande_aar', 'status', )
    date_hierarchy = 'oppretta'
    search_fields = ('=id', '=kid', 'medlem__pk', 'medlem__fornamn',
                     'medlem__etternamn',)
    list_filter = (
        'status',
        filters.GiroSporjingFilter,
        'gjeldande_aar',
        'innbetalt',
        'hensikt',
        'konto',
        'belop',
        filters.MedlemFodtFilter,
        'medlem__lokallag',
        'medlem__status',
        'medlem__utmeldt_dato',
        'medlem__innmeldt_dato',
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
                admin_actions.giro_status_ventar,
                admin_actions.giro_list,
                admin_actions.csv_list,
                admin_actions.pdf_giro,
            ]

    def medlem_admin_change(self, obj):
        return obj.medlem.admin_change()
    medlem_admin_change.short_description = _("Medlem")
    medlem_admin_change.admin_order_field = 'medlem'
    medlem_admin_change.allow_tags = True


class RolleAdmin(CompareVersionAdmin):
    list_filter = ('rolletype', 'lokallag')
    list_display = ('id', 'medlem_admin_change', 'lokallag', 'rolletype')
    raw_id_fields = ('medlem', 'lokallag')

    def medlem_admin_change(self, obj):
        return obj.medlem.admin_change()
    medlem_admin_change.short_description = _("Medlem")
    medlem_admin_change.admin_order_field = 'medlem'
    medlem_admin_change.allow_tags = True


class RolletypeAdmin(CompareVersionAdmin):
    list_display = ('namn', 'rolle_num')
    inlines = [RolleInline,]


class PostNummerAdmin(CompareVersionAdmin):
    list_display = ('__unicode__', 'postnr', 'poststad',
                    'num_teljande_medlem', 'num_medlem', 'folketal',
                    'bydel', 'kommune', 'fylke', 'sist_oppdatert')
    list_filter = ('fylke', 'datakvalitet')
    date_hierarchy = 'sist_oppdatert'
    list_per_page = 400


admin.site.register(models.Medlem, MedlemAdmin)
admin.site.register(models.Lokallag, LokallagAdmin)
admin.site.register(models.Val, ValAdmin)
admin.site.register(models.Giro, GiroAdmin)
admin.site.register(models.LokallagOvervaking, LokallagOvervakingAdmin)
admin.site.register(models.Rolletype, RolletypeAdmin)
admin.site.register(models.Rolle, RolleAdmin)
admin.site.register(models.PostNummer, PostNummerAdmin)
