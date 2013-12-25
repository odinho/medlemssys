# -*- coding: utf-8 -*-
# vim: ts=4 sts=4 expandtab ai

from django import forms
from django.db.models import Q
from django.shortcuts import render

from medlem.models import Giro
from .views import send_ventande_rekningar

class GiroSearch(forms.Form):
    search_data = forms.CharField(widget=forms.Textarea(
                      attrs={'class': 'vLargeTextField',
                             'rows': 25}))

def send(request):
    if request.method == 'POST':
        sende = send_ventande_rekningar()
        successful = [r for r in sende if r.status == '1']
        unsuccessful = [r for r in sende if r.status != '1']
        return render(request, 'admin/giro/send_done.html', {
                'successful': successful,
                'unsuccessful': unsuccessful })
    ventar = Giro.objects.filter(status='V').select_related('medlem')
    return render(request, 'admin/giro/send.html', {
        'ventar': ventar,
        'title': "Send ventande giroar",
    })

def manual_girosearch(request):
    if request.method == 'POST':
        form = GiroSearch(request.POST)
        form.is_valid()
        giroar = []
        giropk_set = set()
        for line in form.cleaned_data['search_data'].split():
            try:
                line = int(line.strip())
            except:
                giroar.append({'search': line, 'error': "Kunne ikkje gjera om til tal"})
                continue
            giro = Giro.objects.filter(
                Q(kid=line) |
                Q(pk=line) |
                Q(medlem__pk=line))
            if not giro:
                giroar.append({'search': line, 'error': "Fann ikkje giro"})
            else:
                giropk_set.add(str(giro[0].pk))
                giroar.append({'search': line, 'giro': giro[0]})
        admin_url = '/admin/medlem/giro/?id__in={0}'.format(','.join(giropk_set))
        return render(request, 'admin/manual_girosearch.html', {
            'admin_url': admin_url,
            'form': form,
            'giroar': giroar,
            'title': u"Manuelt girosøk",
        })
    else:
        form = GiroSearch()
    return render(request, 'admin/manual_girosearch.html', {
        'form': form,
        'title': "Manuelt girosøk",
    })
