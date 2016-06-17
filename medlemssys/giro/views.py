# -*- coding: utf-8 -*-
# vim: ts=4 sts=4 expandtab ai

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
import smtplib

from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.template import Context
from django.template import Template

from medlemssys.medlem.models import Giro
from .models import GiroTemplate

@transaction.atomic
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
    return ventar

def send_rekning(giro):
    subject, text_content, html_content = generate_text("medlemspengar",
                                            {"medlem": giro.medlem, "giro": giro})

    msg = EmailMultiAlternatives(subject,
            body=text_content,
            to=[ giro.medlem.epost ])
    msg.attach_alternative(html_content, "text/html")
    msg.send()

def generate_text(trigger, context):
    tmpl = GiroTemplate.objects.get(trigger=trigger)

    subject = Template(tmpl.subject).render(Context(context))
    text_content = Template(tmpl.text_template).render(Context(context))
    html_content = Template(tmpl.html_template).render(Context(context))

    return (subject, text_content, html_content)
