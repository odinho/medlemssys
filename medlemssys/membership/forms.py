from django import forms
from django.utils.timezone import now

from .models import MembershipType

class MassMembershipForm(forms.Form):
    type = forms.ModelChoiceField(queryset=MembershipType.objects.all())
    start = forms.SplitDateTimeField(initial=now)
    end = forms.SplitDateTimeField(required=False)

    only_membershipless = forms.BooleanField(required=False, initial=True)
