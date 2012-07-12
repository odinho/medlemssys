# -*- coding: utf-8 -*-
# vim: ts=4 sts=4 expandtab ai

from django.template import Context, Template
from django.core.mail import EmailMultiAlternatives

from models import GiroTemplate

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
