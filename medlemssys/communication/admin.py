# -*- coding: utf-8 -*-
# vim: ts=4 sts=4 expandtab ai
from django.contrib import admin

from .models import Email
from .models import Communication
from .models import CommunicationIntent
from .models import CommunicationTemplate

class CommunicationIntentAdmin(admin.ModelAdmin):
    list_display = ('pk', 'prefer', 'template', 'status')
admin.site.register(CommunicationIntent, CommunicationIntentAdmin)

class CommunicationAdmin(admin.ModelAdmin):
    list_display = ('pk', 'intent', 'medlem', 'type', 'giro', 'processed')
    raw_id_fields = ('intent', 'medlem', 'giro', 'email')
admin.site.register(Communication, CommunicationAdmin)

class EmailAdmin(admin.ModelAdmin):
    list_display = ('subject', 'to', 'sent', 'auto_send', 'communication')
admin.site.register(Email, EmailAdmin)

class CommunicationTemplateAdmin(admin.ModelAdmin):
    list_display = ('subject', 'trigger', )
admin.site.register(CommunicationTemplate, CommunicationTemplateAdmin)
