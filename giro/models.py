# -*- coding: utf-8 -*-
# vim: ts=4 sts=4 expandtab ai

from django.db import models

class GiroTemplate(models.Model):
    subject = models.CharField(max_length=100)
    text_template = models.TextField()
    html_template = models.TextField()

    trigger = models.CharField(max_length=100, unique=True)

    def __unicode__(self):
        return self.subject
