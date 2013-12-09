# -*- coding: utf-8 -*-
# vim: ts=4 sw=4 sts=4 expandtab ai

import reversion
from django.contrib.admin import helpers
from django.db.models import Q
from django.template.response import TemplateResponse
from django.utils.translation import ugettext as _

from .forms import MassMembershipForm
from .models import Membership


def create_membership(modeladmin, request, queryset):
    if request.POST.get('post'):
        form = MassMembershipForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['only_membershipless']:
                queryset = queryset.invalid_membership()
            memberships = []
            with reversion.create_revision():
                reversion.set_comment(_("Create memberships"))
                reversion.set_user(request.user)
                for m in queryset:
                    ms = Membership(
                        member=m, type=form.cleaned_data['type'],
                        start=form.cleaned_data['start'],
                        end=form.cleaned_data['end'])
                    ms.save()
                    memberships.append(ms)
                # Doesn't work with reversion
                #Membership.objects.bulk_create(memberships)
                return
    else:
        form = MassMembershipForm()

    opts = modeladmin.model._meta
    app_label = opts.app_label

    context = {
        'title': _("Create membership"),
        'queryset': queryset,
        'opts': opts,
        'app_label': app_label,
        'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
        'action': 'create_membership',
        'n_already_memberships': queryset.valid_membership().count(),
        'form': form,
    }

    return TemplateResponse(request, 'admin/create_membership.html',
            context,
            current_app=modeladmin.admin_site.name)
#communicate_giro.short_description = _("Communicate about these giros")
