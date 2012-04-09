# -*- coding: utf-8 -*-
# vim: ts=4 sts=4 expandtab ai
from django.http import HttpResponse
import datetime, json

from medlemssys.medlem.models import Lokallag
from models import LokallagStat

def update(request):
    lokallag = Lokallag.objects.all()

    llstat = []
    for llag in lokallag:
        teljande_list = list(llag.medlem_set.teljande().values_list('pk', flat=True))
        interessante_list = list(llag.medlem_set.interessante().values_list('pk', flat=True))
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
    return HttpResponse(unicode(llstat), content_type="text/plain; charset=utf-8")
