# -*- coding: utf-8 -*-
# vim: ts=4 sw=4 sts=4 expandtab ai

# Copyright 2009-2014 Odin Hørthe Omdal

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
import csv
import datetime
import os
from cStringIO import StringIO

from reversion import revisions as reversion

from django.conf import settings
from django.contrib.admin import helpers
from django.db import transaction
from django.db.models.query import QuerySet
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.template import Context, Template
from django.template.response import TemplateResponse
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.utils.encoding import force_text
from reportlab.lib.units import cm #, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet

from medlemssys.innhenting import mod10
from medlemssys.giro.models import GiroTemplate
from medlemssys.medlem.models import Giro

import admin # reversion
from .forms import GiroForm
from .forms import SuggestedLokallagForm


@transaction.atomic
def members_meld_ut(modeladmin, request, queryset):
    today = timezone.now().date()
    with reversion.create_revision():
        reversion.set_comment("Meld ut medlemar")
        reversion.set_user(request.user)
        for m in queryset:
            if not m.utmeldt_dato:
                m.utmeldt_dato = today
            if not m.fornamn.lower().startswith('utmeld'):
                m.fornamn = u'UTMELD ' + m.fornamn
            m.save()
members_meld_ut.short_description = "Meld ut"


def simple_member_list(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'filename=medlemer.csv'

    year = datetime.date.today().year
    dc = csv.writer(response, quoting=csv.QUOTE_ALL)
    dc.writerow(["Namn",
                 u"Fødd".encode('utf-8'),
                 "Heimeadresse",
                 "Postadresse",
                 "Poststad",
                 "Mobiltelefon",
                 "Epost",
                 "Lokallag",
                 "Medlemsnummer",
                 "Giro %d" % (year-1),
                 "Betalt",
                 u"Beløp".encode('utf-8'),
                 "KID"])
    def get_giro(year):
        giro = m.gjeldande_giro(year)
        if giro:
            return (giro.innbetalt_belop, giro.belop, giro.kid)
        return ('-', '-', '')
    for m in queryset:
        innbetalt, belop, kid = get_giro(year)
        ifjor = get_giro(year-1)
        postadr, poststad = '', ''
        adr = m.full_postadresse(namn=False, as_list=True)
        if len(adr) == 1:
            poststad = adr[0]
        elif len(adr) > 1:
            postadr = ', '.join(adr[:-1])
            poststad = adr[-1]
        a = [m,
             m.fodt,
             m.full_adresse(namn=False),
             postadr,
             poststad,
             m.mobnr,
             m.epost,
             m.lokallag_display(),
             m.id,
             "%s/%s (%s)" % ifjor,
             innbetalt,
             belop,
             kid]
        dc.writerow([unicode(s).encode('utf-8') for s in a])
    return response
simple_member_list.short_description = "Enkel medlemsliste"


def csv_list(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'filename=dataliste.csv'

    dc = csv.writer(response)
    dc.writerow(model_to_dict(queryset[0]).keys())
    for m in queryset:
        row = []
        for k, v in model_to_dict(m).items():
            if isinstance(v, QuerySet):
                v = ', '.join(force_text(k) for k in v)
            row.append(unicode(v).encode('utf-8'))
        dc.writerow(row)
    return response
csv_list.short_description = "Full dataliste"


def giro_list(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'filename=giroar.csv'

    dc = csv.writer(response, quoting=csv.QUOTE_ALL)
    dc.writerow(["Namn",
                 "Heimeadresse",
                 "Postadresse",
                 "Poststad",
                 "Betalt",
                 "Dato",
                 "Lokallag",
                 u"Fødd".encode('utf-8'),
                 "Epost",
                 "Mobnr",
                 u"For år".encode('utf-8'),
                 "Korleis",
                 "KID",
                 u"Beløp".encode('utf-8'),
                 "Medlem-ID",
                 "Giro-ID",
                 ])
    for g in queryset:
        postadr, poststad = '', ''
        adr = g.medlem.full_postadresse(namn=False, as_list=True)
        if len(adr) == 1:
            poststad = adr[0]
        elif len(adr) > 1:
            postadr = ', '.join(adr[:-1])
            poststad = adr[-1]

        a = [g.medlem,
             g.medlem.full_adresse(namn=False),
             postadr,
             poststad,
             g.innbetalt_belop,
             g.innbetalt,
             g.medlem.lokallag_display(),
             g.medlem.fodt,
             g.medlem.epost,
             g.medlem.mobnr,
             g.gjeldande_aar,
             g.konto,
             g.kid,
             g.belop,
             g.medlem.id,
             g.pk]

        dc.writerow([unicode(s).encode('utf-8') for s in a])

    return response
giro_list.short_description = "Enkel giroliste"


@transaction.atomic
def pdf_giro(modeladmin, request, queryset):
    # User has already written some text, make PDF
    if request.POST.get('post'):
        pdfmetrics.registerFont(TTFont('OCRB', os.path.dirname(__file__) + '/../giro/OCRB.ttf'))
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'filename=girosending.pdf'

        buf = StringIO()

        # Create the PDF object, using the StringIO object as its "file."
        pdf = canvas.Canvas(buf)

        if not request.POST.get('ink-utmeld'):
            queryset = queryset.filter(medlem__utmeldt_dato__isnull=True)
        if not request.POST.get('ink-betalt'):
            queryset = queryset.exclude(innbetalt__isnull=False)

        for giro in queryset:
            m = giro.medlem
            if not giro:
                continue
            context = Context({
                'medlem': m,
                'giro': giro,
                'host': settings.DEFAULT_HOST,
                'email': settings.DEFAULT_EMAIL,
            })
            if request.POST.get('pdf_type') == 'medlemskort':
                pdf = _giro(pdf, request, context)
                pdf = _medlemskort(pdf, request, context)
            elif request.POST.get('pdf_type') == 'giro':
                pdf = _giro_info(pdf, request, context)
                pdf = _giro(pdf, request, context)
            else:
                pdf = _giro_faktura(pdf, request, context)
            pdf.showPage()
            if request.POST.get('merk-postlagt'):
                giro.status = 'M'
                giro.save()

        # Close the PDF object cleanly.
        pdf.save()

        # Get the value of the StringIO buffer and write it to the response.
        pdf = buf.getvalue()
        buf.close()
        response.write(pdf)
        return response

    opts = modeladmin.model._meta
    app_label = opts.app_label
    n_utmelde = queryset.filter(medlem__utmeldt_dato__isnull=False).count()
    n_betalte = queryset.filter(innbetalt__isnull=False).count()
    g_frist = datetime.date.today() + datetime.timedelta(30)
    try:
        template = GiroTemplate.objects.get(trigger="medlemspengar-pdf")
        suggested_title = template.subject
        suggested_text = template.html_template
    except GiroTemplate.DoesNotExist:
        suggested_title = ""
        suggested_text = ""

    title = _("Lag giro-PDF-ar ({c} giroar)".format(c=queryset.count()))

    context = {
        "title": title,
        "queryset": queryset,
        "opts": opts,
        "app_label": app_label,
        "action_checkbox_name": helpers.ACTION_CHECKBOX_NAME,
        "n_utmelde": n_utmelde,
        "n_betalte": n_betalte,
        "g_frist": g_frist,
        "suggested_title": suggested_title,
        "suggested_text": suggested_text,
    }

    request.current_app = modeladmin.admin_site.name
    return TemplateResponse(request, 'admin/pdf_giro.html', context)
pdf_giro.short_description = "Lag giro-PDF"


def _pdf_p(pdf, text, x, y, size_w=None, size_h=None):
    if not size_w:
        size_w = 19
    if not size_h:
        size_h = size_w

    style = getSampleStyleSheet()['BodyText']
    p = Paragraph(text, style)
    used_w, used_h = p.wrap(size_w*cm, size_h*cm)
    p.wrapOn(pdf, size_w*cm, size_h*cm)
    p.drawOn(pdf, x*cm, y*cm - used_h)


def _giro_faktura(pdf, request, context):
    giro = context['giro']
    m = context['medlem']

    title = Template(request.POST.get('title')).render(context)
    pdf.setFont('Helvetica', 16)
    pdf.drawString(1.0*cm, 16*cm, u"%s" % title)

    pdf.setFontSize(11)
    text = request.POST.get('text')
    text_content = Template(text).render(context).replace('\n', '<br/>')
    _pdf_p(pdf, text_content, 1, 15.5, size_w=19, size_h=13)
    _pdf_p(pdf, m.full_betalingsadresse().replace('\n', '<br/>\n'), 1, 26, size_w=8, size_h=6)
    _pdf_p(pdf, u"""\
        Kundenr: {m.pk}<br/>
        Fakturanr: {g.pk}<br/>
        Fakturadato: {now}<br/>
        Organisasjonsnr: {orgnr}<br/>
        Betalingsfrist: {frist}<br/>
        <br/>
        Til konto: <b>{kontonr}</b><br/>
        KID-nummer: <b>{g.kid}</b><br/>
        Å betala: <b>{g.belop},00</b><br/>
        """.format(m=m,
                   g=giro,
                   kontonr=settings.KONTONUMMER,
                   orgnr=settings.ORGNUMMER,
                   now=datetime.date.today(),
                   frist=request.POST.get('frist')),
        15, 26, size_w=4, size_h=6)
    return pdf


def _medlemskort(pdf, request, context):
    giro = context['giro']
    m = context['medlem']

    # Medlemskort
    pdf.setFont('Helvetica', 12)
    pdf.drawString(13.0*cm, 14.9*cm, u"%s" % unicode(m))

    pdf.setFont('OCRB', 11)

    pdf.drawString(13.8*cm, 14.3*cm, u"%s" % m.pk)
    pdf.drawString(18.1*cm, 14.3*cm, u"%s" % giro.gjeldande_aar)
    pdf.drawString(13.0*cm, 12.7*cm, u"%s" % giro.belop)
    pdf.drawString(14.8*cm, 12.7*cm, u"%s" % '00')
    return pdf


def _giro_info(pdf, request, context):
    title = Template(request.POST.get('title')).render(context)

    pdf.setFont('OCRB', 11)
    pdf.drawString(1.2*cm, 8.3*cm, u"%s" % title)

    tekst = pdf.beginText(11.4*cm, 5.5*cm)
    for adrdel in settings.ORG_ADR.split('\n'):
        tekst.textLine(adrdel.strip())
    pdf.drawText(tekst)

    return pdf

def _giro(pdf, request, context):
    giro = context['giro']
    m = context['medlem']
    title = Template(request.POST.get('title')).render(context)

    pdf.setFont('Helvetica', 16)
    pdf.drawString(1.0*cm, 26*cm, u"%s" % title)
    pdf.setFontSize(12)

    text_template = Template(request.POST.get('text'))
    text_content = text_template.render(context).replace('\n', '<br/>')

    _pdf_p(pdf, text_content, 1, 25.5, size_w=18, size_h=13)

    pdf.setFont('OCRB', 11)
    # Giro
    tekst = pdf.beginText(1.9*cm, 6.0*cm)
    for adrdel in m.full_betalingsadresse().split('\n'):
        tekst.textLine(adrdel.strip())
    pdf.drawText(tekst)
    if giro.betalt() or (giro.hensikt == 'P' and m.har_betalt()):
        pdf.drawString(18*cm, 12.8*cm, "BETALT")
        pdf.setFillColorRGB(0, 0, 0)
        pdf.rect(0,  5.3*cm, 26*cm, 0.2*cm, stroke=False, fill=True)
        pdf.rect(0, 4.85*cm, 26*cm, 0.2*cm, stroke=False, fill=True)
        pdf.rect(0,  1.9*cm, 26*cm, 0.2*cm, stroke=False, fill=True)
        pdf.rect(0, 1.45*cm, 26*cm, 0.2*cm, stroke=False, fill=True)
    else:
        pdf.drawString(16.8*cm, 9.5*cm, u"%s" % request.POST.get('frist'))
        pdf.drawString(5.0*cm,  2.08*cm, u"%s" % giro.kid)
        pdf.drawString(8.5*cm,  2.08*cm, u"%s" % giro.belop)
        pdf.drawString(10.6*cm, 2.08*cm, u"%s" % '00')
        pdf.drawString(11.9*cm, 2.08*cm,
                       u"%s" % mod10.mod10(unicode(giro.belop) + '00'))
        pdf.drawString(13.2*cm, 2.08*cm, u"%s" % settings.KONTONUMMER)

    return pdf


@transaction.atomic
def lag_giroar(modeladmin, request, queryset):
    year = datetime.date.today().year
    form = GiroForm(request.POST if 'post' in request.POST else None,
                    initial={'belop':70})
    if not request.POST.get('post') or not form.is_valid():
        opts = modeladmin.model._meta
        app_label = opts.app_label
        n_utmelde = queryset.filter(utmeldt_dato__isnull=False).count()
        n_allereie_giro = queryset.filter(giroar__gjeldande_aar=year).count()

        title = _("Lag giroar")

        context = {
            "title": title,
            "queryset": queryset,
            "form": form,
            "opts": opts,
            "app_label": app_label,
            "action_checkbox_name": helpers.ACTION_CHECKBOX_NAME,
            "n_utmelde": n_utmelde,
            "n_allereie_giro": n_allereie_giro,
        }

        request.current_app = modeladmin.admin_site.name
        return TemplateResponse(request, "admin/lag_giroar.html", context)

    if not request.POST.get("ink-utmeld"):
        queryset = queryset.filter(utmeldt_dato__isnull=True)
    if not request.POST.get("ink-betalt"):
        queryset = queryset.exclude(giroar__gjeldande_aar=year)

    with reversion.create_revision():
        reversion.set_comment("Opprett giroar admin action")
        reversion.set_user(request.user)
        data = form.cleaned_data
        for m in queryset:
            g = Giro(belop=data['belop'], konto=data['konto'],
                     desc=data['desc'], hensikt=data['hensikt'],
                     medlem=m)
            g.save()
lag_giroar.short_description = "Opprett giroar"


def giro_status_ferdig(modeladmin, request, queryset):
    with reversion.create_revision():
        reversion.set_comment("Giro status ferdig admin action")
        reversion.set_user(request.user)
        today = datetime.date.today()
        for g in queryset:
            g.status='F'
            if not g.innbetalt_belop:
                g.innbetalt_belop = g.belop
            if not g.innbetalt:
                g.innbetalt = today
            g.save()
giro_status_ferdig.short_description = "Sett giro betalt"


def giro_status_postlagt(modeladmin, request, queryset):
    with reversion.create_revision():
        for g in queryset:
            g.status='M'
            g.save()
        reversion.set_comment("Giro status postlagt admin action")
        reversion.set_user(request.user)
giro_status_postlagt.short_description = "Sett girostatus 'Manuelt postlagt'"


def giro_status_ventar(modeladmin, request, queryset):
    with reversion.create_revision():
        for g in queryset:
            g.status='V'
            g.save()
        reversion.set_comment("Giro status ventar admin action")
        reversion.set_user(request.user)
giro_status_ventar.short_description = "Sett girostatus 'Ventar'"


def giro_status_ubetalt(modeladmin, request, queryset):
    with reversion.create_revision():
        for g in queryset:
            g.status='U'
            g.save()
        reversion.set_comment("Giro status 'utgått ubetalt' admin action")
        reversion.set_user(request.user)
giro_status_ubetalt.short_description = "Sett girostatus 'Utgått ubetalt'"


def giro_hensikt_gaave(modeladmin, request, queryset):
    with reversion.create_revision():
        for g in queryset:
            g.hensikt='G'
            g.save()
        reversion.set_comment("Giro hensikt 'gaave' admin action")
        reversion.set_user(request.user)
giro_hensikt_gaave.short_description = u"Sett hensikt 'Gåve'"


def giro_hensikt_medlemspengar(modeladmin, request, queryset):
    with reversion.create_revision():
        for g in queryset:
            g.hensikt='P'
            g.save()
        reversion.set_comment("Giro hensikt 'medlemspengar' admin action")
        reversion.set_user(request.user)
giro_hensikt_medlemspengar.short_description = u"Sett hensikt 'Medlemspengar'"


@transaction.atomic
def suggest_lokallag(modeladmin, request, queryset):
    if request.POST.get('post'):
        updated = []
        with reversion.create_revision():
            reversion.set_comment("Endra lokallag med suggest_lokallag")
            reversion.set_user(request.user)
            for m in queryset:
                pk = "lokallag_{0}".format(m.pk)
                if pk not in request.POST:
                    continue
                try:
                    new_lokallag_id = int(request.POST[pk])
                except ValueError:
                    continue
                if m.lokallag_id == new_lokallag_id:
                    continue
                m.lokallag_id = new_lokallag_id
                m.save()
                updated.append(m)
        modeladmin.message_user(
            request,
            "{} brukarar med oppdaterte lokallag".format(len(updated)))
        return None
    already_ok = []
    suggested_new = []
    totally_new = []
    nothing = []
    for m in queryset:
        m.prop = m.proposed_lokallag()
        if m.prop and m.lokallag == m.prop[0]:
            already_ok.append(m)
        elif m.lokallag in m.prop:
            suggested_new.append(m)
        elif m.prop:
            totally_new.append(m)
        else:
            nothing.append(m)

        choices = [(l.pk, l.namn) for l in m.prop]
        if m.lokallag and m.lokallag not in m.prop:
            choices.append((m.lokallag_id, m.lokallag.namn))
        elif not m.lokallag:
            choices.append(('', '(ingen)'))
        m.suggested = SuggestedLokallagForm(
                          auto_id='id_{}_%s'.format(m.pk),
                          initial={
                              'lokallag': m.lokallag_id,
                              'medlem': m.pk,
                          },
                          lokallag_choices=choices,
                          medlem_id=m.pk)

    title = _("Endra lokallag ({c} medlemar)".format(c=queryset.count()))
    opts = modeladmin.model._meta
    app_label = opts.app_label
    context = {
        "title": title,
        "queryset": queryset,
        "opts": opts,
        "app_label": app_label,
        "action": 'suggest_lokallag',
        "action_checkbox_name": helpers.ACTION_CHECKBOX_NAME,
        "already_ok": already_ok,
        "suggested_new": suggested_new,
        "totally_new": totally_new,
    }
    request.current_app = modeladmin.admin_site.name
    return TemplateResponse(request, "admin/proposed_lokallag.html",
              context)
suggest_lokallag.short_description = _(u"Foreslå lokallag")
