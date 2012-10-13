# -*- coding: utf-8 -*-
# vim: ts=4 sw=4 sts=4 expandtab ai
from django.contrib.admin import helpers
from django.http import HttpResponse
from django.forms.models import model_to_dict
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext as _
from django.template.response import TemplateResponse
import csv

def simple_member_list(self, request, queryset):
    from medlemssys.medlem.models import PostNummer
    response = HttpResponse(mimetype="text/csv; charset=utf-8")
    response['Content-Disposition'] = 'filename=medlemer.csv'

    dc = csv.writer(response, quoting=csv.QUOTE_NONNUMERIC)
    dc.writerow(["Namn",
                 "Adresse",
                 "Postnr",
                 "Stad",
                 "Mobiltelefon",
                 u"Født".encode("utf-8"),
                 "Lokallag",
                 "Betalt?"])
    for m in queryset:
        try:
            stad = PostNummer.objects.get(postnr=m.postnr).poststad
        except PostNummer.DoesNotExist:
            stad = "?"

        a = [m,
             m.postadr,
             m.postnr,
             stad,
             m.mobnr,
             m.fodt,
             m.lokallag_display(),
             m.har_betalt()]

        dc.writerow([unicode(s).encode("utf-8") for s in a])

    return response
def csv_member_list(self, request, queryset):
    response = HttpResponse(mimetype="text/csv; charset=utf-8")
    response['Content-Disposition'] = 'filename=medlemer.csv'

    dc = csv.writer(response)
    dc.writerow(model_to_dict(queryset[0]).keys())
    for m in queryset:
        a = model_to_dict(m).values()
        dc.writerow([unicode(s).encode("utf-8") for s in a])

    return response

def pdf_member_list(self, request, queryset):
    # User has already written some text, make PDF
    if request.POST.get('post'):
        from cStringIO import StringIO
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import cm #, mm

        response = HttpResponse(mimetype="application/pdf")
        response['Content-Disposition'] = 'filename=noko.pdf'

        buf = StringIO()

        # Create the PDF object, using the StringIO object as its "file."
        pdf = canvas.Canvas(buf)

        # Draw things on the PDF. Here's where the PDF generation happens.
        # See the ReportLab documentation for the full list of functionality.
        for m in queryset:
            pdf.setFontSize(16)
            pdf.drawString(1.5*cm, 24*cm, "%s" % request.POST.get('title'))

            pdf.setFontSize(10)
            infotekst = pdf.beginText(1.5*cm, 22*cm)
            infotekst.textOut("%s" % request.POST.get('text'))
            pdf.drawText(infotekst)

            pdf.setFontSize(10)
            tekst = pdf.beginText(1.5*cm, 6*cm)
            tekst.textLine("%s %s" % (m.fornamn, m.etternamn) )
            tekst.textLine("%s" % (m.postadr,) )
            tekst.textLine("%s" % (m.postnr,) )
            pdf.drawText(tekst)

            pdf.showPage()
            print "%s %s" % (m.fornamn, request.POST.get('title'))

        # Close the PDF object cleanly.
        pdf.save()

        # Get the value of the StringIO buffer and write it to the response.
        pdf = buf.getvalue()
        buf.close()
        response.write(pdf)
        print "Returning response!!"
        return response

    opts = self.model._meta
    app_label = opts.app_label
    if len(queryset) == 1:
        objects_name = force_unicode(opts.verbose_name)
    else:
        objects_name = force_unicode(opts.verbose_name_plural)

    title = _("PDF-info")

    context = {
        "title": title,
        "objects_name": objects_name,
        'queryset': queryset,
        "opts": opts,
        "app_label": app_label,
        'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
    }

    return TemplateResponse(request, 'admin/pdf_info.html', context,
            current_app=self.admin_site.name)

