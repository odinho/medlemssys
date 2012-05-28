# -*- coding: utf-8 -*-
# vim: ts=4 sts=4 expandtab ai
from django.db import IntegrityError
from django.http import HttpResponse
import datetime, json, re, operator

from medlemssys.medlem.models import Lokallag, Medlem
from models import LokallagStat

def update_lokallagstat():
    lokallag = Lokallag.objects.all()

    llstat = []
    LokallagStat.objects.filter(veke="{0:%Y-%W}".format(datetime.datetime.now())).delete()

    for llag in lokallag:
        teljande_list = list(llag.medlem_set.teljande().values_list('pk', flat=True))
        interessante_list = list(llag.medlem_set.interessante().values_list('pk', flat=True))
        try:
            llstat.append(LokallagStat.objects.create(
                    lokallag = llag,
                    veke = "{0:%Y-%W}".format(datetime.datetime.now()),

                    teljande = json.dumps(teljande_list),
                    interessante = json.dumps(interessante_list),

                    n_teljande = llag.medlem_set.teljande().count(),
                    n_interessante = llag.medlem_set.interessante().count(),
                    n_ikkje_utmelde = llag.medlem_set.ikkje_utmelde().count(),
                    n_totalt = llag.medlem_set.count(),
                ))
        except IntegrityError:
            pass # Already have this week

    return llstat

from collections import defaultdict
from django.shortcuts import render_to_response

def vervetopp_json(request):
    nye = Medlem.objects.filter(oppretta__year=2012, status='M')

    count = defaultdict(lambda: [])
    for n in nye:
        pers = re.sub("(?i)Verva av ", "", n.innmeldingsdetalj).title()

        count[pers].append(
            dict(namn=str(n),
                lokallag=str(n.lokallag),
                teljande=n.er_teljande(),
                betalt=n.har_betalt()
            ))

    return HttpResponse(unicode(json.dumps(count)).encode('utf8'),
            content_type="application/json; charset=utf-8")

from django.views.decorators.clickjacking import xframe_options_exempt

@xframe_options_exempt
def vervetopp(request):
    vervarar = Medlem.objects.filter(har_verva__innmeldt_dato__gte="2012-04-25",
            har_verva__innmeldt_dato__lte="2012-06-30",
            status="M").distinct()

    nye_vervarar = sorted(vervarar, key=lambda v: (v.har_verva.teljande().count(), v.har_verva.potensielt_teljande().count()), reverse=True)

    return render_to_response('statistikk/vervetopp-embed.html', dict(objects=nye_vervarar))

@xframe_options_exempt
def vervometer(request):
    teljande = Medlem.objects.teljande().filter(innmeldt_dato__gte="2012-04-25",
            innmeldt_dato__lte="2012-06-30").distinct().count()
    potensielt_teljande = Medlem.objects.potensielt_teljande().filter(innmeldt_dato__gte="2012-04-25",
            innmeldt_dato__lte="2012-06-30").distinct().count()
    maal = 300

    gjenstaande = maal - (teljande + potensielt_teljande)

    return render_to_response('statistikk/vervometer-embed.html',
                              {
                                 'teljande': teljande,
                                 'potensielt_teljande': potensielt_teljande,
                                 'maal': maal,
                                 'gjenstaande': gjenstaande,
                              })
