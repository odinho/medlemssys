# -*- coding: utf-8 -*-
# vim: ts=4 sw=4 sts=4 expandtab ai

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
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count
from django.shortcuts import render_to_response, get_object_or_404

from models import Medlem, Lokallag


@login_required
def home(request):
    lokallag = Lokallag.objects.annotate(num_medlemar=Count('medlem'))  \
                               .filter(num_medlemar__gt=0)              \
                               .order_by("-num_medlemar")

    return render_to_response('lokallag/lokallag_listing.html', {
        'lokallag': lokallag,
    })


def lokallag_home(request, slug):
    lokallag = get_object_or_404(Lokallag, slug=slug)

    if not request.user.is_staff:
        if request.user.is_authenticated():
            try:
                medlem = request.user.medlem
            except ObjectDoesNotExist:
                return render_to_response(
                    "error.html",
                    {
                        'message': "Brukaren din er ikkje kopla opp mot ein "
                        "medlemsprofil. Det må til for å få løyve til å sjå "
                        "ting."
                    })
        elif request.GET.get('user_id'):
            medlem = get_object_or_404(Medlem, pk=request.GET['user_id'])
            if (not medlem.nykel or medlem.nykel != request.GET.get('nykel')):
                return redirect_to_login(request.get_full_path())
        else:
            return redirect_to_login(request.get_full_path())
        if not medlem.lokallagsrolle.filter(slug=slug).exists():
            return render_to_response(
                "error.html",
                {'message': "Du har inga rolle i dette lokallaget."})

    medlem = Medlem.objects.interessante().filter(lokallag=lokallag)
    betalt_count = Medlem.objects.betalande().filter(lokallag=lokallag).count()
    teljande_count = Medlem.objects.teljande().filter(lokallag=lokallag).count()

    return render_to_response('lokallag/lokallag_home.html', {
        'lokallag': lokallag,
        'medlem': medlem,
        'betalt_count': betalt_count,
        'teljande_count': teljande_count,
    })
