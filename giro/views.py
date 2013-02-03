# -*- coding: utf-8 -*-
# vim: ts=4 sts=4 expandtab ai

import smtplib

from django.template import Context, Template
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.db.models import F

from medlemssys.medlem.models import Giro
from models import GiroTemplate

@transaction.commit_on_success
def send_ventande_rekningar():
    ventar = Giro.objects.filter(status='V').select_related('medlem')
    for v in ventar:
        if v.betalt():
            v.status = 'F'
        elif not v.medlem.epost or len(v.medlem.epost) < 6:
            v.status = 'E'
        else:
            try:
                send_rekning(v)
                v.status = "1"
            except smtplib.SMTPRecipientsRefused:
                # TODO Do logging
                continue
        v.save()

def send_rekning(giro):
    subject, text_content, html_content = generate_text("medlemspengar",
                                            {"medlem": giro.medlem, "giro": giro})

    msg = EmailMultiAlternatives(subject,
            text_content,
            "skriv@nynorsk.no",
            [ giro.medlem.epost ])
    msg.attach_alternative(html_content, "text/html")
    msg.send()

def generate_text(trigger, context):
    tmpl = GiroTemplate.objects.get(trigger=trigger)

    subject = Template(tmpl.subject).render(Context(context))
    text_content = Template(tmpl.text_template).render(Context(context))
    html_content = Template(tmpl.html_template).render(Context(context))

    return (subject, text_content, html_content)
