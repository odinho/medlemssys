# -*- coding: utf-8 -*-
# vim: ts=4 sts=4 expandtab ai
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

import datetime

from django import forms
from django.db.models import Q
from django.shortcuts import render

from medlemssys.medlem.models import Giro
from medlemssys.medlem.models import Medlem
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

def gaaver(request):
    try:
        over = int(request.GET['over'])
    except:
        over = 500
    year = request.GET.get('aar', datetime.date.today().year)
    p = {}
    for g in Giro.objects.filter(
            innbetalt_belop__gt=0, gjeldande_aar=year, hensikt='G'):
        p[g.medlem.pk] = p.get(g.medlem.pk, 0) + g.innbetalt_belop
    over_amount = {id: b for id, b in p.items() if b>=over}
    medlemar = Medlem.objects.filter(id__in=over_amount.keys())
    objects = [(m, over_amount[m.pk]) for m in medlemar]
    admin_url = '/admin/medlem/medlem/?id__in=%s' % (
        ','.join(str(k) for k in over_amount.keys()))
    return render(request, 'admin/giro/gaaver.html', {
        'objects': objects,
        'admin_url': admin_url,
        'title': u"Medlem med gåver over {over} for {year}".format(
            over=over, year=year),
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
