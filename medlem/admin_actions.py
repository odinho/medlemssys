# -*- coding: utf-8 -*-
# vim: ts=4 sw=4 sts=4 expandtab ai
import csv
import datetime

from django.contrib.admin import helpers
from django.http import HttpResponse
from django.forms.models import model_to_dict
from django.utils.translation import ugettext as _
from django.template.response import TemplateResponse

def simple_member_list(self, request, queryset):
    response = HttpResponse(mimetype="text/csv; charset=utf-8")
    response['Content-Disposition'] = 'filename=medlemer.csv'

    dc = csv.writer(response, quoting=csv.QUOTE_ALL)
    dc.writerow(["Namn",
                 "Adresse",
                 "Postnr",
                 "Stad",
                 "Mobiltelefon",
                 "Epost",
                 u"Født".encode("utf-8"),
                 "Lokallag",
                 "Betalt?"])
    for m in queryset:
        postadr = m.postadr
        if m.ekstraadr:
            postadr += u"\n{0}".format(m.ekstraadr)

        a = [m,
             postadr,
             m.postnr,
             m.stad,
             m.mobnr,
             m.epost,
             m.fodt,
             m.lokallag_display(),
             m.har_betalt()]

        dc.writerow([unicode(s).encode("utf-8") for s in a])

    return response
simple_member_list.short_description = "Enkel medlemsliste"

def csv_member_list(self, request, queryset):
    response = HttpResponse(mimetype="text/csv; charset=utf-8")
    response['Content-Disposition'] = 'filename=medlemer.csv'

    dc = csv.writer(response)
    dc.writerow(model_to_dict(queryset[0]).keys())
    for m in queryset:
        a = model_to_dict(m).values()
        dc.writerow([unicode(s).encode("utf-8") for s in a])

    return response
csv_member_list.short_description = "Full medlemsliste"

def pdf_giro(self, request, queryset):
    # User has already written some text, make PDF
    if request.POST.get('post'):
        from cStringIO import StringIO
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import cm #, mm
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        from medlemssys.mod10 import mod10

        pdfmetrics.registerFont(TTFont('OCRB', 'giro/OCRB.ttf'))
        response = HttpResponse(mimetype="application/pdf")
        response['Content-Disposition'] = 'filename=girosending.pdf'

        buf = StringIO()

        # Create the PDF object, using the StringIO object as its "file."
        pdf = canvas.Canvas(buf)

        if not request.POST.get("ink-utmeld"):
            queryset = queryset.filter(utmeldt_dato__isnull=True)

        # Draw things on the PDF. Here's where the PDF generation happens.
        # See the ReportLab documentation for the full list of functionality.
        for m in queryset:
            giro = m.gjeldande_giro()

            pdf.setFont('Helvetica', 16)
            pdf.drawString(1.0*cm, 26*cm, u"%s" % request.POST.get('title'))

            pdf.setFontSize(11)
            infotekst = pdf.beginText(1.0*cm, 25*cm)
            infotekst.textOut(u"%s" % request.POST.get('text'))
            pdf.drawText(infotekst)

            pdf.setFont('OCRB', 11)
            tekst = pdf.beginText(1.2*cm, 5.5*cm)
            tekst.textLine(u"%s %s" % (m.fornamn, m.etternamn) )
            tekst.textLine(u"%s" % (m.postadr,) )
            tekst.textLine(u"%s %s" % (m.postnr, m.stad) )
            pdf.drawText(tekst)

            pdf.drawString(13*cm, 12.8*cm, u"%s" % giro.belop)
            pdf.drawString(15*cm, 12.8*cm, u"%s" % '00')
            pdf.drawString(14*cm, 14.2*cm, u"%s" % m.pk)
            pdf.drawString(18.3*cm, 14.2*cm, u"%s" % giro.gjeldande_aar)

            pdf.drawString(17.1*cm, 9.3*cm, u"%s" % request.POST.get('frist'))

            pdf.drawString(5.0*cm,  1.58*cm, u"%s" % giro.kid)
            pdf.drawString(8.5*cm,  1.58*cm, u"%s" % giro.belop)
            pdf.drawString(10.6*cm, 1.58*cm, u"%s" % '00')
            pdf.drawString(11.9*cm, 1.58*cm,
                           u"%s" % mod10(unicode(giro.belop) + '00'))
            pdf.drawString(13.2*cm, 1.58*cm, u"%s" % '3450 65 48618')

            pdf.showPage()

        # Close the PDF object cleanly.
        pdf.save()

        # Get the value of the StringIO buffer and write it to the response.
        pdf = buf.getvalue()
        buf.close()
        response.write(pdf)
        return response

    opts = self.model._meta
    app_label = opts.app_label
    n_utmelde = queryset.filter(utmeldt_dato__isnull=False).count()
    g_frist = datetime.date.today() + datetime.timedelta(30)

    title = _("Lag giro-PDF-ar")

    context = {
        "title": title,
        "queryset": queryset,
        "opts": opts,
        "app_label": app_label,
        "action_checkbox_name": helpers.ACTION_CHECKBOX_NAME,
        "n_utmelde": n_utmelde,
        "g_frist": g_frist,
    }

    return TemplateResponse(request, "admin/pdf_giro.html", context,
            current_app=self.admin_site.name)
pdf_giro.short_description = "Lag giro-PDF"


def lag_giroar(self, request, queryset):
    from medlemssys.medlem.models import Giro

    year = datetime.date.today().year
    if not request.POST.get('post'):
        opts = self.model._meta
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
                current_app=self.admin_site.name)

    if not request.POST.get("ink-utmeld"):
        queryset = queryset.filter(utmeldt_dato__isnull=True)

    queryset = queryset.exclude(giroar__gjeldande_aar=year)

    for m in queryset:
        g = Giro(belop=request.POST.get('belop'), medlem=m)
        g.save()
lag_giroar.short_description = "Opprett giroar"

