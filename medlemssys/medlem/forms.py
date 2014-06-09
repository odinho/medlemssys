# -*- coding: utf-8 -*-
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
from django import forms
from models import Giro

class GiroForm(forms.ModelForm):
    class Meta:
        model = Giro
        fields = ('belop', 'konto', 'hensikt', 'desc', 'status')

class SuggestedLokallagForm(forms.Form):
    lokallag = forms.ChoiceField(choices=[('', '---')],
                                 widget=forms.RadioSelect())

    class Meta:
        fields = ('lokallag',)

    def __init__(self, *args, **kwargs):
        choices = kwargs.pop('lokallag_choices')
        medlem_id = kwargs.pop('medlem_id')
        new_name = 'lokallag_{}'.format(medlem_id)
        super(type(self), self).__init__(*args, **kwargs)
        self.initial[new_name] = self.initial.pop('lokallag')
        self.fields[new_name] = self.fields.pop('lokallag')
        self.fields[new_name].choices = choices
