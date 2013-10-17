
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
