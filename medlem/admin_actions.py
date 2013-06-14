# -*- coding: utf-8 -*-
# vim: ts=4 sw=4 sts=4 expandtab ai
import csv
import datetime

import reversion

from django.conf import settings
from django.contrib.admin import helpers
from django.db import transaction
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.template import Context, Template
from django.template.response import TemplateResponse
from django.utils.translation import ugettext as _

import admin # reversion

def simple_member_list(modeladmin, request, queryset):
    response = HttpResponse(mimetype="text/csv; charset=utf-8")
    response['Content-Disposition'] = 'filename=medlemer.csv'

    dc = csv.writer(response, quoting=csv.QUOTE_ALL)
    dc.writerow(["Namn",
                 u"Fødd".encode("utf-8"),
                 "Heimeadresse",
                 "Postadresse",
                 "Poststad",
                 "Mobiltelefon",
                 "Epost",
                 "Lokallag",
                 "Betalt"])
    for m in queryset:
        belop = m.gjeldande_giro()
        if belop:
            belop = belop.innbetalt_belop
        if not belop:
            belop = '-'
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
             belop]

        dc.writerow([unicode(s).encode("utf-8") for s in a])

    return response
simple_member_list.short_description = "Enkel medlemsliste"

def csv_list(modeladmin, request, queryset):
    response = HttpResponse(mimetype="text/csv; charset=utf-8")
    response['Content-Disposition'] = 'filename=dataliste.csv'

    dc = csv.writer(response)
    dc.writerow(model_to_dict(queryset[0]).keys())
    for m in queryset:
        a = model_to_dict(m).values()
        dc.writerow([unicode(s).encode("utf-8") for s in a])

    return response
csv_list.short_description = "Full dataliste"

def giro_list(modeladmin, request, queryset):
    response = HttpResponse(mimetype="text/csv; charset=utf-8")
    response['Content-Disposition'] = 'filename=giroar.csv'

    dc = csv.writer(response, quoting=csv.QUOTE_ALL)
    dc.writerow(["Namn",
                 "Adresse",
                 "Betalt",
                 "Dato",
                 "Lokallag",
                 u"Fødd".encode("utf-8"),
                 u"For år".encode("utf-8"),
                 "Korleis",
                 "KID",
                 "Beløp",
                 "Giro-ID",
                 ])
    for g in queryset:

        a = [g.medlem,
             g.medlem.full_adresse(namn=False),
             g.innbetalt_belop,
             g.innbetalt,
             g.medlem.lokallag_display(),
             g.medlem.fodt,
             g.gjeldande_aar,
             g.konto,
             g.kid,
             g.belop,
             g.pk]

        dc.writerow([unicode(s).encode("utf-8") for s in a])

    return response
giro_list.short_description = "Enkel revisorliste"

@transaction.commit_on_success
def pdf_giro(modeladmin, request, queryset):
    # User has already written some text, make PDF
    if request.POST.get('post'):
        import os
        from cStringIO import StringIO
        from reportlab.pdfgen import canvas
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        pdfmetrics.registerFont(TTFont('OCRB', os.path.dirname(__file__) + '/../giro/OCRB.ttf'))
        response = HttpResponse(mimetype="application/pdf")
        response['Content-Disposition'] = 'filename=girosending.pdf'

        buf = StringIO()

        # Create the PDF object, using the StringIO object as its "file."
        pdf = canvas.Canvas(buf)

        if not request.POST.get("ink-utmeld"):
            queryset = queryset.filter(medlem__utmeldt_dato__isnull=True)
        if not request.POST.get("ink-betalt"):
            queryset = queryset.exclude(innbetalt__isnull=False)

        for giro in queryset:
            m = giro.medlem
            if not giro:
                continue
            if request.POST.get('pdf_type') == 'medlemskort':
                pdf = _giro_medlemskort(pdf, request, m, giro)
            else:
                pdf = _giro_faktura(pdf, request, m, giro)
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
    }

    return TemplateResponse(request, "admin/pdf_giro.html", context,
            current_app=modeladmin.admin_site.name)
pdf_giro.short_description = "Lag giro-PDF"


def _pdf_p(pdf, text, x, y, size_w=None, size_h=None):
    from reportlab.lib.units import cm #, mm
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import getSampleStyleSheet

    if not size_w:
        size_w = 19
    if not size_h:
        size_h = size_w

    style = getSampleStyleSheet()['BodyText']
    p = Paragraph(text, style)
    used_w, used_h = p.wrap(size_w*cm, size_h*cm)
    p.wrapOn(pdf, size_w*cm, size_h*cm)
    p.drawOn(pdf, x*cm, y*cm - used_h)

def _giro_faktura(pdf, request, m, giro):
    from reportlab.lib.units import cm #, mm

    pdf.setFont('Helvetica', 16)
    pdf.drawString(1.0*cm, 16*cm, u"%s" % request.POST.get('title'))

    pdf.setFontSize(11)
    text = request.POST.get('text')
    text_content = Template(text).render(Context({'medlem': m, 'giro': giro})).replace('\n', '<br/>')
    _pdf_p(pdf, text_content, 1, 15.5, size_w=19, size_h=13)
    _pdf_p(pdf, m.full_betalingsadresse().replace('\n', '<br/>\n'), 1, 26, size_w=8, size_h=6)
    _pdf_p(pdf, u"""\
        Kundenr: {m.pk}<br/>
        Fakturanr: {g.pk}<br/>
        Fakturadato: {now}<br/>
        Betalingsfrist: {frist}<br/>
        Til konto: <b>{kontonr}</b><br/>
        KID-nummer: <b>{g.kid}</b><br/>
        Å betala: <b>{g.belop},00</b><br/>
        """.format(m=m,
                   g=giro,
                   kontonr=settings.KONTONUMMER,
                   now=datetime.date.today(),
                   frist=request.POST.get('frist')),
        15, 26, size_w=4, size_h=6)

    return pdf

def _giro_medlemskort(pdf, request, m, giro):
    from reportlab.lib.units import cm #, mm

    from medlemssys.mod10 import mod10

    pdf.setFont('Helvetica', 16)
    pdf.drawString(1.0*cm, 26*cm, u"%s" % request.POST.get('title'))
    pdf.setFontSize(12)

    text_template = Template(request.POST.get('text'))
    text_context = Context({'medlem': m, 'giro': giro})
    text_content = text_template.render(text_context).replace('\n', '<br/>')

    _pdf_p(pdf, text_content, 1, 25.5, size_w=18, size_h=13)

    pdf.setFont('OCRB', 11)
    tekst = pdf.beginText(1.2*cm, 5.5*cm)
    for adrdel in m.full_betalingsadresse().split('\n'):
        tekst.textLine(adrdel.strip())
    pdf.drawText(tekst)

    pdf.drawString(13*cm, 12.8*cm, u"%s" % giro.belop)
    pdf.drawString(15*cm, 12.8*cm, u"%s" % '00')
    pdf.drawString(14*cm, 14.2*cm, u"%s" % m.pk)
    pdf.drawString(18.3*cm, 14.2*cm, u"%s" % giro.gjeldande_aar)

    if m.har_betalt():
        pdf.drawString(18*cm, 12.8*cm, "BETALT")
        pdf.setFillColorRGB(0, 0, 0)
        pdf.rect(0,  5.3*cm, 26*cm, 0.2*cm, stroke=False, fill=True)
        pdf.rect(0, 4.85*cm, 26*cm, 0.2*cm, stroke=False, fill=True)
        pdf.rect(0,  1.9*cm, 26*cm, 0.2*cm, stroke=False, fill=True)
        pdf.rect(0, 1.45*cm, 26*cm, 0.2*cm, stroke=False, fill=True)
    else:
        pdf.drawString(17.1*cm, 9.3*cm, u"%s" % request.POST.get('frist'))

        pdf.drawString(5.0*cm,  1.58*cm, u"%s" % giro.kid)
        pdf.drawString(8.5*cm,  1.58*cm, u"%s" % giro.belop)
        pdf.drawString(10.6*cm, 1.58*cm, u"%s" % '00')
        pdf.drawString(11.9*cm, 1.58*cm,
                       u"%s" % mod10(unicode(giro.belop) + '00'))
        pdf.drawString(13.2*cm, 1.58*cm, u"%s" % settings.KONTONUMMER)

    return pdf


@transaction.commit_on_success
def lag_giroar(modeladmin, request, queryset):
    from medlemssys.medlem.models import Giro

    year = datetime.date.today().year
    if not request.POST.get('post'):
        opts = modeladmin.model._meta
        app_label = opts.app_label
        n_utmelde = queryset.filter(utmeldt_dato__isnull=False).count()
        n_allereie_giro = queryset.filter(giroar__gjeldande_aar=year).count()

        title = _("Lag giroar")

        context = {
            "title": title,
            "queryset": queryset,
            "opts": opts,
            "app_label": app_label,
            "action_checkbox_name": helpers.ACTION_CHECKBOX_NAME,
            "n_utmelde": n_utmelde,
            "n_allereie_giro": n_allereie_giro,
        }

        return TemplateResponse(request, "admin/lag_giroar.html", context,
                current_app=modeladmin.admin_site.name)

    if not request.POST.get("ink-utmeld"):
        queryset = queryset.filter(utmeldt_dato__isnull=True)

    queryset = queryset.exclude(giroar__gjeldande_aar=year)

    with reversion.create_revision():
        reversion.set_comment("Opprett giroar admin action")
        reversion.set_user(request.user)
        for m in queryset:
            g = Giro(belop=request.POST.get('belop'), medlem=m)
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
