# -*- coding: utf-8 -*-
# vim: ts=4 sw=4 sts=4 expandtab ai
#from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required

from models import Medlem, Tilskiping

@login_required
def listing(request):
    tilskipingar = Tilskiping.objects.all()

    return render_to_response('tilskiping/tilskiping_listing.html', {
        'objects': tilskipingar,
    })

@login_required
def detail(request, slug):
    tilskiping = Tilskiping.objects.get(slug=slug)

    if not request.user.is_staff:
        try:
            medlem_prof = request.user.get_profile()
        except ObjectDoesNotExist:
            return render_to_response("error.html", { 'message': """Brukaren din er
            ikkje kopla opp mot ein medlemsprofil. Det må til for å få løyve til å
            sjå ting.""" })

        if not medlem_prof.tilskiping.filter(slug=slug).exists():
            return render_to_response("error.html", { 'message': "Du var ikkje med på denne tilskipinga." })

    medlem = Medlem.objects.filter(tilskiping=tilskiping)
    betalt_count = Medlem.objects.betalande().filter(tilskiping=tilskiping).count()
    teljande_count = Medlem.objects.teljande().filter(tilskiping=tilskiping).count()

    return render_to_response('tilskiping/tilskiping_home.html', {
        'tilskiping': tilskiping,
        'medlem': medlem,
        'betalt_count': betalt_count,
        'teljande_count': teljande_count,
    })
