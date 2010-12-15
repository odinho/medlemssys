# vim: ts=4 sts=4 expandtab ai
from reversion.admin import VersionAdmin
from django.contrib import admin
from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.forms.models import model_to_dict
from settings import ADMIN_MEDIA_PREFIX
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

class MedlemAdmin(VersionAdmin):
    model_admin_manager = Medlem.objects
    list_display = ('id', '__unicode__', 'lokallag', 'er_innmeldt',
                    'har_betalt', 'fodt_farga')
    list_display_links = ('id', '__unicode__')
    date_hierarchy = 'innmeldt_dato'
    list_filter = ('lokallag', 'fodt')
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
    actions = ['csv_member_list','pdf_member_list',]

    class Media:
        css = {
            "all": (ADMIN_MEDIA_PREFIX + "medlem.css",
                ADMIN_MEDIA_PREFIX + "css/forms.css",)
        }

    def csv_member_list(self, request, queryset):
        liste = ""

        response = HttpResponse(mimetype="text/plain")

        dc = csv.writer(response)
        dc.writerow(model_to_dict(queryset[0]).keys())
        for m in queryset:
            a = model_to_dict(m).values()
            dc.writerow([unicode(s).encode("utf-8") for s in a])

        return response

    def pdf_member_list(self, request, queryset):
        from cStringIO import StringIO
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import cm, mm

        response = HttpResponse(mimetype="application/pdf")
        response['Content-Disposition'] = 'filename=noko.pdf'

        buf = StringIO()

        # Create the PDF object, using the StringIO object as its "file."
        pdf = canvas.Canvas(buf)

        # Draw things on the PDF. Here's where the PDF generation happens.
        # See the ReportLab documentation for the full list of functionality.
        for m in queryset:
            pdf.setFontSize(10)

            tekst = pdf.beginText(1.5*cm, 6*cm)
            tekst.textLine("%s %s" % (m.fornamn, m.etternamn) )
            tekst.textLine("%s" % (m.postadr,) )
            tekst.textLine("%s" % (m.postnr,) )

            pdf.drawText(tekst)

            pdf.showPage()

        # Close the PDF object cleanly.
        pdf.save()

        # Get the value of the StringIO buffer and write it to the response.
        pdf = buf.getvalue()
        buf.close()
        response.write(pdf)

        return response


class MedlemInline(admin.TabularInline):
    model = Medlem
    extra = 3
    fields = ['fornamn', 'etternamn', 'postadr', 'postnr', 'epost', 'mobnr', 'fodt']

class LokallagAdmin(admin.ModelAdmin):
    inlines = [MedlemInline,]

# XXX: Dette fungerer i Django 1.2
#class NemndmedlemskapInline(MedlemInline):
#    model = Medlem.nemnd.through
#class NemndAdmin(admin.ModelAdmin):
#    inlines = [NemndmedlemskapInline,]
#admin.site.register(Nemnd, NemndAdmin)

admin.site.register(Medlem, MedlemAdmin)
admin.site.register(Lokallag, LokallagAdmin)
admin.site.register(Tilskiping)
admin.site.register(Rolletype)
admin.site.register(Nemnd)
admin.site.register(Val)
