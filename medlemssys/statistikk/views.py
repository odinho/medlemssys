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
import datetime
import json
import re
import smtplib
from collections import defaultdict

from django.core.mail import EmailMultiAlternatives
from django.db import IntegrityError
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import loader
from django.utils import timezone
from django.views.decorators.clickjacking import xframe_options_exempt
from reversion.models import Version

from medlemssys.medlem import admin
assert admin # Silence pyflakes
from medlemssys.medlem.models import (
    Lokallag, Medlem, LokallagOvervaking, Val)
from medlemssys.statistikk.models import LokallagStat


def update_lokallagstat(time):
    time = time or timezone.now()
    lokallag = Lokallag.objects.all()

    llstat = []
    LokallagStat.objects.filter(veke="{0:%Y-%W}".format(time)).delete()

    for llag in lokallag:
        teljande_list = list(llag.medlem_set.teljande().values_list('pk', flat=True))
        interessante_list = list(llag.medlem_set.interessante().values_list('pk', flat=True))
        try:
            llstat.append(LokallagStat.objects.create(
                    lokallag = llag,
                    veke = "{0:%Y-%W}".format(time),

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

FROM_DATE="2013-08-19"
TO_DATE="2013-09-29"

@xframe_options_exempt
def vervetopp(request):
    vervarar = Medlem.objects.filter(har_verva__innmeldt_dato__gte=FROM_DATE,
            har_verva__innmeldt_dato__lte=TO_DATE,
            status="M").distinct()

    nye_vervarar = sorted(vervarar, key=lambda v: (v.har_verva.teljande().count(), v.har_verva.potensielt_teljande().count()), reverse=True)

    return render_to_response('statistikk/vervetopp-embed.html', dict(objects=nye_vervarar))

@xframe_options_exempt
def vervometer(request):
    teljande = Medlem.objects.teljande().filter(innmeldt_dato__gte=FROM_DATE,
            innmeldt_dato__lte=TO_DATE).distinct().count()
    potensielt_teljande = Medlem.objects.potensielt_teljande().filter(innmeldt_dato__gte=FROM_DATE,
            innmeldt_dato__lte=TO_DATE).distinct().count()
    maal = 300

    gjenstaande = maal - (teljande + potensielt_teljande)

    return render_to_response('statistikk/vervometer-embed.html',
                              {
                                 'teljande': teljande,
                                 'potensielt_teljande': potensielt_teljande,
                                 'maal': maal,
                                 'gjenstaande': gjenstaande,
                              })
def namn_from_pks(model, val_keys):
    namn = []
    for vk in val_keys:
        namn.append(model.objects.get(pk=vk).namn)
    return namn



def _get_overvakingar():
    for overvak in LokallagOvervaking.objects.filter(
            Q(deaktivert__isnull=True)
            | Q(deaktivert__gt=timezone.now()) ):
        epost_seq = overvak.epostar()
        if not epost_seq:
            # Noone to send to anyway
            continue

        if ((timezone.now() - overvak.sist_oppdatert)
                < datetime.timedelta(days=6, seconds=22*60*60)):
            # Har sendt epost for mindre enn 7 dagar sidan, so ikkje send noko no.
            # TODO: Dette er ein sjukt dårleg måte å gjera dette på, fiks betre
            continue

        sist_oppdatering = overvak.sist_oppdatert
        overvak.sist_oppdatert = timezone.now()

        medlem = overvak.lokallag.medlem_set.alle().filter(oppdatert__gt=sist_oppdatering)
        nye_medlem = list(medlem.filter(oppretta__gt=sist_oppdatering).exclude(status='I'))
        nye_infofolk = list(medlem.filter(oppretta__gt=sist_oppdatering, status='I'))
        # Alle andre, "gamle" medlemar
        medlem = medlem.exclude(oppretta__gt=sist_oppdatering)

        # Finn dei som har flytta til eit ANNA lokallag
        try:
            sist_statistikk = LokallagStat.objects.get(
                                veke="{0:%Y-%W}".format(sist_oppdatering),
                                lokallag=overvak.lokallag)
        except LokallagStat.DoesNotExist:
            sist_statistikk = LokallagStat.objects.filter(
                                oppretta__gt=sist_oppdatering,
                                lokallag=overvak.lokallag
                ).order_by("-oppretta").first()

            #stderr(u"LokallagStat for {0}, {1:%Y-%W} fanst ikkje. Brukar {2}" \
            #            .format(overvak.lokallag,
            #                sist_oppdatering,
            #                sist_statistikk))

        if sist_statistikk:
            medlemar_sist = json.loads(sist_statistikk.interessante)
            medlemar_no = overvak.lokallag.medlem_set.interessante().values_list('pk', flat=True)
            vekkflytta_medlem = Medlem.objects.filter(
                                    pk__in=set(medlemar_sist) - set(medlemar_no),
                                    utmeldt_dato__isnull=True)
        else:
            vekkflytta_medlem = []


        tilflytta_medlem, utmeld_medlem, endra_medlem, ukjend_endring = [], [], [], []
        for m in medlem:
            try:
                old = (Version.objects.get_for_object(m)
                       .filter(revision__date_created__lte=sist_oppdatering)
                       .order_by('-revision__date_created')[0])
            except IndexError:
                continue
            new = Version.objects.get_for_object(m)[0]

            def _changed_field(k):
                if old.field_dict[k] == new.field_dict[k]:
                    return False
                if (old.field_dict[k] in (None, '', 'None') and
                        new.field_dict[k] in (None, '', 'None')):
                    return False
                if (isinstance(old.field_dict[k], basestring) and
                        "".join(old.field_dict[k].split())
                        == "".join(new.field_dict[k].split())):
                    return False
                return True
            changed_keys = filter(_changed_field, new.field_dict.keys())

            def _humanify_pks(field, model):
                if field in changed_keys:
                    old.field_dict[field] = ", ".join(
                        namn_from_pks(model, map(int, old.field_dict[field])))
                    new.field_dict[field] = ", ".join(
                        namn_from_pks(model, map(int, new.field_dict[field])))
            _humanify_pks('val', Val)

            m.changed = [ (k, old.field_dict[k], new.field_dict[k])
                          for k in changed_keys
                          if k not in ["_siste_medlemspengar",
                                       "innmeldingstype",
                                       "oppdatert",
                                       "oppretta",
                                       "nykel",
                                      ]]
            if 'utmeldt_dato' in changed_keys and new.field_dict['utmeldt_dato']:
                utmeld_medlem.append(m)
            elif 'lokallag' in changed_keys:
                tilflytta_medlem.append(m)
            elif 'status' in changed_keys and old.field_dict['status'] == 'I':
                nye_medlem.append(m)
            elif m.changed:
                endra_medlem.append(m)
            else:
                ukjend_endring.append(m)
        if not (len(nye_medlem) + len(nye_infofolk) +
                len(tilflytta_medlem) + len(endra_medlem) +
                len(utmeld_medlem) + len(vekkflytta_medlem)):
            # Ikkje send noko dersom det er ingenting å melda
            continue
        ctx = {
            'nye_medlem': nye_medlem,
            'nye_infofolk': nye_infofolk,
            'endra_medlem': endra_medlem,
            'utmeld_medlem': utmeld_medlem,
            'ukjend_endring': ukjend_endring,
            'tilflytta_medlem': tilflytta_medlem,
            'vekkflytta_medlem': vekkflytta_medlem,
        }
        yield epost_seq, overvak, sist_oppdatering, ctx


def send_overvakingar():
    for epost_seq, overvak, sist_oppdatering, ctx in _get_overvakingar():
        msg = create_overvaking_email(
                epost_seq,
                overvak,
                overvak.lokallag,
                sist_oppdatering,
                **ctx)
        try:
            msg.send()
        except smtplib.SMTPRecipientsRefused:
            # TODO Do logging
            continue
        overvak.save()
    return "Ferdig"


def create_overvaking_email(epost_seq, overvaking, lokallag, sist_oppdatering, **ctx):
        context = ctx.copy()
        context.update({
          'dagar': (timezone.now() - sist_oppdatering).days,
          'lokallag': lokallag,
          'overvaking': overvaking,
        })

        text_content = (loader
                        .get_template('epostar/lokallag_overvaking.txt')
                        .render(context))
        html_content = (loader
                        .get_template('epostar/lokallag_overvaking.html')
                        .render(context))
        emne = (loader
                .get_template('epostar/lokallag_overvaking_emnefelt.txt')
                .render(context))
        msg = EmailMultiAlternatives(" ".join(emne.split())[:-1], text_content, "skriv@nynorsk.no", epost_seq)
        msg.attach_alternative(html_content, "text/html")

        return msg
