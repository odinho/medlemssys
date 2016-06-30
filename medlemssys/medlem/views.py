# -*- coding: utf-8 -*-
# vim: ts=4 sts=4 expandtab ai

# Copyright 2009-2016 Odin Hørthe Omdal

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
import json

from reversion import revisions as reversion
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.db.models import Q
from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.http import HttpResponseRedirect
from django.shortcuts import render

from models import EndraMedlemForm
from models import InnmeldingMedlemForm
from models import Lokallag
from models import Medlem
from models import Val


def create_medlem(request):
    if request.method == 'POST':
        form = InnmeldingMedlemForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/takk/')
    else:
        form = InnmeldingMedlemForm()

    return render(request, 'medlem/create.html', {
        'form': form,
    })


def edit_medlem(request, id, nykel):
    forbid = False
    try:
        m = Medlem.objects.get(pk=id)
    except Medlem.DoesNotExist:
        forbid = True
    if forbid or nykel != m.nykel:
        return HttpResponseForbidden("<h1>Medlemen finst ikkje, "
                                     "eller nykelen er feil</h1>")
    if request.method == 'POST':
        form = EndraMedlemForm(request.POST, instance=m)
        post_val = request.POST.get('val_epost', '')
        post_val += request.POST.get('val_post', '')
        post_val += request.POST.get('val_tlf',  '')
        post_val += request.POST.get('val_nyhendebrev',  '')
        if form.is_valid():
            with reversion.create_revision():
                added = []
                removed = []
                for tittel in ('Ikkje epost', u'Ikkje Motmæle', 'Ikkje ring',
                               'Ikkje Norsk Tidend', 'Ikkje nyhendebrev'):
                               #'Ikkje lokallagsepost', 'Ikkje SMS', 'Ikkje nyhendebrev'):
                    val_obj = Val.objects.get(tittel=tittel)
                    if tittel in post_val:
                        if not m.val_exists(tittel):
                            added.append(tittel)
                        m.val.add(val_obj)
                    else:
                        if m.val_exists(tittel):
                            removed.append(tittel)
                        m.val.remove(val_obj)
                comment = "Brukar oppdaterte {0}.".format(form.changed_data)
                if added:
                    comment += " La til: {0}.".format(added)
                if removed:
                    comment += " Tok vekk: {0}.".format(removed)
                reversion.set_comment(comment)
                form.save()
    else:
        form = EndraMedlemForm(instance=m)

    return render(request, 'medlem/edit.html', {
       'object': m,
       'form': form,
    })


@login_required
def ringjelister(request):
    lokallag = Lokallag.objects.all().order_by('andsvar')

    return render(request, 'medlem/ringjeliste.html', {
        'lokallag': lokallag,
    })


@login_required
def search(request):
    return render(request, 'medlem/search.html', {})


def get_members(terms, limit=20):
    search = None

    # Søk etter mobil- eller medlemsnummer
    if "".join(terms).isdigit():
        q = "".join(terms)
        search = Q(mobnr__startswith=q) | Q(id__startswith=q)
        terms = []

    # Vanleg søk
    for q in terms:
        search_part = (
            Q(fornamn__istartswith=q) |
            Q(mellomnamn__istartswith=q) |
            Q(etternamn__istartswith=q) |
            Q(fodt__icontains=q) |
            Q(lokallag__namn__icontains=q) |
            Q(lokallag__slug__istartswith=q))
        if not search:
            search = search_part
        else:
            search = search & search_part

    results = (Medlem.objects.select_related('lokallag')
               .prefetch_related('giroar')
               .annotate(null_last=Count('_siste_medlemspengar'))
               .order_by('-null_last', '-_siste_medlemspengar', '-fodt', 'pk'))
    if search:
        results = results.filter(search)
    return results[:limit]


@login_required
def get_members_json(request):
    term = request.GET.get('term', '')
    results = []
    for member in get_members(term.split()):
        member_json = {}
        member_json['id'] = member.pk
        member_json['namn'] = str(member)
        member_json['alder'] = member.alder()
        if member.lokallag_id:
            member_json['lokallag'] = str(member.lokallag)
        else:
            member_json['lokallag'] = "(ingen)"
        bet = (giro.gjeldande_aar for giro in
               member.giroar.order_by('-gjeldande_aar') if
               giro.innbetalt)
        member_json['bet'] = [unicode(x) for x in bet]
        results.append(member_json)
    data = json.dumps(results)
    mimetype = 'application/json'
    return HttpResponse(data, mimetype)
