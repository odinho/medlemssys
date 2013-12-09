# -*- coding: utf-8 -*-
# vim: ts=4 sts=4 expandtab ai
from django.contrib import admin
from reversion_compare.admin import CompareVersionAdmin

from .models import Membership, MembershipType

class MembershipAdmin(CompareVersionAdmin):
    list_display = ('member', 'type', 'start', 'end',)
    raw_id_fields = ('member', )
admin.site.register(Membership, MembershipAdmin)

class MembershipTypeAdmin(CompareVersionAdmin):
    list_display = ('name', 'default_price', 'num_memberships')
admin.site.register(MembershipType, MembershipTypeAdmin)
