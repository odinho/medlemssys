# -*- coding: utf-8 -*-
# vim: ts=4 sw=4 sts=4 expandtab ai
#from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.db.models import Count

from models import Medlem, Lokallag

@login_required
def home(request):
    lokallag = Lokallag.objects.annotate(num_medlemar=Count('medlem')).filter(num_medlemar__gt=0)

    return render_to_response('lokallag/lokallag_listing.html', {
        'lokallag': lokallag,
    })

@login_required
def lokallag_home(request, slug):
    lokallag = Lokallag.objects.get(slug=slug)

    return render_to_response('lokallag/lokallag_home.html', {
        'lokallag': lokallag,
    })

@login_required
def medlemsliste(request, slug):
    lokallag = Lokallag.objects.get(slug=slug)

    if not request.user.is_staff:
        try:
            medlem_prof = request.user.get_profile()
        except ObjectDoesNotExist:
            return render_to_response("error.html", { 'message': """Brukaren din er
            ikkje kopla opp mot ein medlemsprofil. Det må til for å få løyve til å
            sjå ting.""" })

        if not medlem_prof.lokallagsrolle.filter(slug=slug).exists():
            return render_to_response("error.html", { 'message': "Du har inga rolle i dette lokallaget." })

    medlem = Medlem.interessante.filter(lokallag=lokallag)
    betalt_count = Medlem.teljande.filter(lokallag=lokallag).count()

    return render_to_response('lokallag/medlemsliste.html', {
        'lokallag': lokallag,
        'medlem': medlem,
        'betalt_count': betalt_count,
    })
