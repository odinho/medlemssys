# -*- coding: utf-8 -*-
# vim: ts=4 sts=4 expandtab ai
from django.db import IntegrityError
from django.http import HttpResponse
import datetime, json, re, operator

from medlemssys.medlem.models import Lokallag, Medlem
from models import LokallagStat

def update(request):
    lokallag = Lokallag.objects.all()

    llstat = []
    LokallagStat.objects.filter(veke="{:%Y-%W}".format(datetime.datetime.now())).delete()

    for llag in lokallag:
        teljande_list = list(llag.medlem_set.teljande().values_list('pk', flat=True))
        interessante_list = list(llag.medlem_set.interessante().values_list('pk', flat=True))
        try:
            llstat.append(LokallagStat.objects.create(
                    lokallag = llag,
                    veke = "{:%Y-%W}".format(datetime.datetime.now()),

                    teljande = json.dumps(teljande_list),
                    interessante = json.dumps(interessante_list),

                    n_teljande = llag.medlem_set.teljande().count(),
                    n_interessante = llag.medlem_set.interessante().count(),
                    n_ikkje_utmelde = llag.medlem_set.ikkje_utmelde().count(),
                    n_totalt = llag.medlem_set.count(),
                ))
        except IntegrityError:
            print "Already have this week"
            return HttpResponse("Har allereie denne veka", content_type="text/plain; charset=utf-8")
    return HttpResponse(unicode(llstat), content_type="text/plain; charset=utf-8")

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

def vervetopp(request):
    nye = Medlem.objects.filter(oppretta__year=2012, status='M')

    count = defaultdict(lambda: dict(verva=[], bet_teljande=[], ubet_teljande=[], totalt=0))
    for n in nye:
        pers = re.sub("(?i)Verva av ", "", n.innmeldingsdetalj).title()
        count[pers]['namn'] = pers
        count[pers]['totalt'] += 1

        if n.er_teljande() and n.har_betalt():
            count[pers]['bet_teljande'].append(n)
        elif n.er_teljande() and not n.har_betalt():
            count[pers]['ubet_teljande'].append(n)
        else:
            count[pers]['verva'].append(n)

    newlist = sorted(count.values(), key=lambda x: (-len(x['bet_teljande']), -len(x['ubet_teljande'])))

    return render_to_response('statistikk/vervetopp.html', dict(objects=newlist))
