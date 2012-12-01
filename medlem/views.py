# vim: ts=4 sw=4 expandtab ai
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required

from models import Medlem, InnmeldingMedlemForm, Lokallag

def create_medlem(request):
    if request.method == 'POST':
        form = InnmeldingMedlemForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/takk/')
    else:
        form = InnmeldingMedlemForm()

    return render_to_response('create_medlem.html', {
        'form': form,
    })

@login_required
def ringjelister(request):
    lokallag = Lokallag.objects.all().order_by('andsvar')
    Medlem.objects.filter()

    return render_to_response('medlem/ringjeliste.html', {
        'lokallag': lokallag,
    })

@login_required
def search(request):
    return render_to_response('medlem/search.html', {})

import json
from django.db.models import Q

def get_members(terms, limit=20):
    search = None
    for q in terms:
        search_part = Q(fornamn__icontains=q)   \
        | Q(mellomnamn__icontains=q)            \
        | Q(etternamn__icontains=q)             \
        | Q(fodt__icontains=q)                  \
        | Q(lokallag__namn__icontains=q)

        if not search:
            search = search_part
        else:
            search = search & search_part

    if search:
        return Medlem.objects.select_related('giroar').filter(search)[:limit]

    return Medlem.objects.select_related('giroar')[:limit]

def get_members_json(request):
    term = request.GET.get('term', '')
    results = []
    for member in get_members(term.split()):
        member_json = {}
        member_json['id'] = member.pk
        member_json['namn'] = str(member)
        member_json['alder'] = member.alder()
        member_json['lokallag'] = str(member.lokallag)
        bet = member.giroar.filter(innbetalt__isnull=False).values_list("oppretta", flat=True)
        member_json['bet'] = [x.year for x in bet]
        results.append(member_json)
    data = json.dumps(results)
    mimetype = 'application/json'
    return HttpResponse(data, mimetype)
