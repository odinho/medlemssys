# -*- coding: utf-8 -*-
# vim: ts=4 sts=4 expandtab ai
from django import forms
from django.core.mail import EmailMultiAlternatives
from django.db import models
from django.utils.translation import ugettext_lazy as _

from medlem.models import Medlem
from medlem.models import Giro

class CommunicationIntent(models.Model):
    TYPE_EMAIL = 'email'
    TYPE_PDF = 'pdf'
    TYPES = (
        (TYPE_EMAIL, _('Email')),
        (TYPE_PDF, _('PDF')),
    )

    STATUS_WAITING = 'waiting'
    STATUS_PROCESSED = 'processed'
    STATUS_FINISHED = 'finished'
    STATUSES = (
        (STATUS_WAITING, _('Waiting')),
        (STATUS_PROCESSED, _('Processed')),
        (STATUS_FINISHED, _('Finished')),
    )

    prefer = models.CharField(
        max_length=20, choices=TYPES, default=TYPE_EMAIL)
    template = models.ForeignKey('CommunicationTemplate')
    status = models.CharField(
        max_length=20, choices=STATUSES, default=STATUS_WAITING)

    created = models.DateTimeField(auto_now_add=True)

    def process(self):
        emails = self.communication_set.filter(
            type=self.TYPE_EMAIL,
        )
        for e in emails:
            e.email.send()

        pdf_pages = self.communication_set.filter(
            type=self.TYPE_PDF,
        )
        pass

    def __unicode__(self):
        return u"Intent {s.prefer} '{s.template}'".format(s=self)


class Communication(models.Model):
    intent = models.ForeignKey(CommunicationIntent)
    medlem = models.ForeignKey(Medlem)
    type = models.CharField(
        max_length=20, choices=CommunicationIntent.TYPES)

    # This could be an extra object contenttype
    # But let's make it simple for now
    giro = models.ForeignKey(Giro, blank=True, null=True)

    # This depends on the type
    email = models.OneToOneField('Email', blank=True, null=True)
    pdf = models.OneToOneField('Pdf', blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True)
    processed = models.DateTimeField(blank=True, null=True)

    @staticmethod
    def create_from_intent(intent, medlem, giro=None):
        if medlem.epost and intent.prefer == intent.TYPE_EMAIL:
            email = Email.create_from_template(
                intent.template, medlem, giro)
            email.save()
            obj = Communication(
                intent=intent, medlem=medlem, type=intent.TYPE_EMAIL,
                email=email)
        else:
            obj = Communication(
                intent=intent, medlem=medlem, type=intent.TYPE_PDF)
        if giro:
            obj.giro = giro
        return obj

    def __unicode__(self):
        return u"{t} to {s.medlem}".format(
                s=self, t=self.get_type_display())

class Pdf(models.Model):
    LAYOUT_GIRO = 'giro'
    LAYOUT_FAKTURA = 'faktura'
    LAYOUTS = (
        (LAYOUT_GIRO, _('Giro')),
        (LAYOUT_FAKTURA, _('Faktura')),
    )
    header = models.CharField(max_length=255)
    text_body = models.TextField()

    layout = models.CharField(
        max_length=20, choices=LAYOUTS, default=LAYOUT_GIRO)



class Email(models.Model):
    subject = models.CharField(max_length=255)
    to = models.EmailField()
    text_body = models.TextField()
    html_body = models.TextField(blank=True, null=True)

    sent = models.DateTimeField(blank=True, null=True)
    auto_send = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def create_from_template(template, medlem, giro=None):
        from django.template import Template, Context

        ctx = Context({'medlem': medlem, 'giro': giro})
        subject = Template(template.subject).render(ctx)
        text_body = Template(template.text_template).render(ctx)

        obj = Email(
            subject=subject, to=medlem.epost, text_body=text_body)
        return obj

    def send(self):
        msg = EmailMultiAlternatives(self.subject,
                body=self.text_body,
                to=self.to)
        if self.html_body:
            msg.attach_alternative(self.html_body, "text/html")
        msg.send()

    def __unicode__(self):
        return u"{s.subject} ({s.to})".format(s=self)

class CommunicationTemplate(models.Model):
    subject = models.CharField(max_length=100)
    text_template = models.TextField()

    html_template = models.TextField(blank=True, null=True)
    pdf_template = models.TextField(blank=True, null=True)

    trigger = models.CharField(max_length=100, unique=True)

    def __unicode__(self):
        return u"{}".format(self.subject)


class CommunicationIntentForm(forms.ModelForm):
    class Meta:
        model = CommunicationIntent
        fields = ('template', 'prefer')
