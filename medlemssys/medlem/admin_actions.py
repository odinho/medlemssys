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
from .forms import SuggestedLokallagForm

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
def communicate_giro(modeladmin, request, queryset):
    from communication.models import Communication, CommunicationIntentForm
    if request.POST.get('post'):
        form = CommunicationIntentForm(request.POST)
        if form.is_valid():
            if not request.POST.get("ink-utmeld"):
                queryset = queryset.filter(medlem__utmeldt_dato__isnull=True)
            if not request.POST.get("ink-betalt"):
                queryset = queryset.exclude(innbetalt__isnull=False)

            form.save()
            for giro in queryset:
                com = Communication.create_from_intent(
                    form.instance, medlem=giro.medlem, giro=giro)
                com.save()
            return None
    else:
        # Clean form, no post
        form = CommunicationIntentForm()

    opts = modeladmin.model._meta
    app_label = opts.app_label
    n_utmelde = queryset.filter(medlem__utmeldt_dato__isnull=False).count()
    n_betalte = queryset.filter(innbetalt__isnull=False).count()
    g_frist = datetime.date.today() + datetime.timedelta(30)


    title = _("Communicate ({c} giros)".format(c=queryset.count()))

    context = {
        "title": title,
        "queryset": queryset,
        "opts": opts,
        "app_label": app_label,
        "action_checkbox_name": helpers.ACTION_CHECKBOX_NAME,
        "n_utmelde": n_utmelde,
        "n_betalte": n_betalte,
        "g_frist": g_frist,
        "form": form,
    }

    return TemplateResponse(request, "admin/communicate_giro.html", context,
            current_app=modeladmin.admin_site.name)
communicate_giro.short_description = _("Communicate about these giros")

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




@transaction.commit_on_success
def lag_giroar(modeladmin, request, queryset):
    from medlem.models import Giro

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


@transaction.commit_on_success
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
    return TemplateResponse(request, "admin/proposed_lokallag.html",
              context, current_app=modeladmin.admin_site.name)
suggest_lokallag.short_description = _(u"Foreslå lokallag")
