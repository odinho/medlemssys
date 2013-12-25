from django.contrib import admin

from models import GiroTemplate

class GiroTemplateAdmin(admin.ModelAdmin):
    list_display = ('subject', 'trigger')

admin.site.register(GiroTemplate, GiroTemplateAdmin)
