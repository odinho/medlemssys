# -*- coding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from dateutil.parser import parse
import datetime
#from django.shortcuts import render_to_response

from medlemssys.settings import MEDLEM_CSV, GIRO_CSV, LAG_CSV
from medlemssys.medlem.models import Medlem, Lokallag, Giro, Tilskiping, LokallagOvervaking
from medlemssys.medlem.models import update_denormalized_fields
from medlemssys.medlem import admin # Needed to register reversion
import csv

import reversion

# REGISTERKODE,LAGSNR,MEDLNR,FORNAMN,MELLOMNAMN,ETTERNAMN,TILSKRIFT1,TILSKRIFT2,POST,VERVA,VERV,LP,GJER,MERKNAD,KJØNN,INN,INNMEDL,UTB,UT_DATO,MI,MEDLEMINF,TLF_H,TLF_A,E_POST,H_TILSKR1,H_TILSKR2,H_POST,H_TLF,Ring_B,Post_B,MM_B,MNM_B,BRUKHEIME,FARRETOR,RETUR,REGBET,HEIMEADR,REGISTRERT,TILSKRIFT_ENDRA,FØDEÅR,Epost_B
nmu_csv_map = {
        'MEDLNR': 'id',
        'FORNAMN': 'fornamn',
        'MELLOMNAMN': 'mellomnamn',
        'ETTERNAMN': 'etternamn',
        'FØDEÅR': 'fodt',
        'POST': 'postnr',
        'TILSKRIFT1': 'postadr',
        'TILSKRIFT2': 'ekstraadr',
        'INN': 'innmeldt_dato',
        'UT_DATO': 'utmeldt_dato',
        'MI': 'status',
        'E_POST': 'epost',
        'TLF_H': 'mobnr',
        'TLF_A': 'heimenr',
        'LAGSNR': 'lokallag',
        'KJØNN': 'kjon',
        'GJER': 'gjer',
        'VERVA': 'innmeldingsdetalj',
        'MERKNAD': 'merknad',
    }

VAL = (
        (40, 0, 'Ikkje epost'), # EPOST_B = 40
        (28, 0, 'Ikkje ring'), # RING_B = 28
        (29, 0, 'Ikkje post'), # POST_B = 29
        (30, 0, 'Ikkje Motmæle'), # MM_B = 30
        (31, 0, 'Ikkje Norsk Tidend'), # MNM_B = 31
)

def fraa_nmu_csv(request):
    def do_work():
        for i in import_lag():
            if settings.DEBUG:
                print "Lag: %s" % unicode(i)

            yield "Lag: %s\n" % unicode(i)

        for i in import_medlem():
            if settings.DEBUG:
                print "Medlem: %s" % unicode(i)

            yield "Medlem: %s\n" % unicode(i)

        for i in import_bet():
            if settings.DEBUG:
                print "Betaling: %s" % unicode(i)

            yield "Betaling: %s\n" % unicode(i)

        fiks_tilskipingar()

        update_denormalized_fields()

        send_epostar()

    #return HttpResponse(do_work(), content_type="text/plain; charset=utf-8")
    return HttpResponse(send_epostar(), content_type="text/plain; charset=utf-8")

#@reversion.create_revision() XXX There's a bug here somewhere
@transaction.commit_on_success
def import_medlem():
    liste = csv.reader(open(MEDLEM_CSV))
    mapping = nmu_mapping(headers=liste.next())

    with reversion.create_revision():
        reversion.set_comment("Import frå Access")

        for num, rad in enumerate(liste):
            tmp = {}
            for typ in nmu_csv_map.values():
                tmp[typ] = rad[mapping[typ]] \
                            .decode("utf-8") \
                            .replace(r"\n", "\n")

            try:
                tmp['lokallag_id'] = int(tmp['lokallag'])
            except (KeyError, ValueError):
                pass
            finally:
                del tmp['lokallag']

            try:
                tmp['fodt'] = int(tmp['fodt'])
            except ValueError:
                del tmp['fodt']

            try:
                tmp['postnr'] = format(int(tmp['postnr']), "04d")
            except ValueError:
                del tmp['postnr']

            if len(tmp.get('status', '')) > 1:
                #print "%s(%s) status too long: %s" % (tmp['id'], tmp['fornamn'], tmp['status'])
                tmp['status'] = tmp['status'][0]

            if len(tmp.get('kjon', '')) > 1:
                #print "%s(%s) kjon too long: %s" % (tmp['id'], tmp['fornamn'], tmp['kjon'])
                tmp['kjon'] = tmp['kjon'][0]

            tmp['oppretta'] = parse(tmp['innmeldt_dato'],
                    default=datetime.datetime(1980, 1, 1, 0, 0))
            tmp['innmeldt_dato'] = tmp['oppretta'].date()
            tmp['oppdatert'] = datetime.datetime.now()

            if len(tmp['utmeldt_dato']) > 2:
                tmp['utmeldt_dato'] = parse(tmp['utmeldt_dato'], default=None)
                if hasattr(tmp['utmeldt_dato'], 'date'):
                    tmp['utmeldt_dato'] = tmp['utmeldt_dato'].date()
            else:
                del tmp['utmeldt_dato']

            #print "%s(%s) utmdato:%s stat:%s" % (tmp['id'], tmp['fornamn'], tmp.get('utmeldt_dato',
            #    'g0ne'), tmp.get('status', 'g0ne'))
            m = Medlem(**tmp)
            m.save()

            for v in VAL:
                if int(rad[v[0]]) == int(v[1]):
                    m.set_val(v[2])

            # Print first 200 names
            if num < 199:
                yield u"{0:>3}. {1}".format(unicode(num), unicode(m))

            elif num%200 == 0 and num != 0:
                transaction.commit()
                yield unicode(num)


def nmu_mapping(headers):
    mapping = dict()
    for h in nmu_csv_map.keys():
        if h in headers:
            mapping[nmu_csv_map[h]] = headers.index(h)

    return mapping

# csv: DIST,FLAG,LLAG,lid,ANDSVAR,LOKALSATS
# model: namn, fylkeslag, distrikt, andsvar
@reversion.create_revision()
@transaction.commit_on_success
def import_lag():
    reversion.set_comment("Import frå Access")
    liste = csv.reader(open(LAG_CSV))
    liste.next()
    alle_lag = {}

    for rad in liste:
        lag = Lokallag(pk=rad[3],
                namn=rad[2].decode('utf-8').capitalize(),
                fylkeslag=rad[1].decode('utf-8'), distrikt=rad[0].decode('utf-8'),
                andsvar=rad[4].decode('utf-8'))
        lag.save()

        alle_lag[rad[3]] = lag

    return alle_lag

# csv: MEDLNR,BETALT,KONTO,KONTONAMN,DATO,AR,SUM,BETID
# model (giro): medlem, belop, kid, oppretta, innbetalt, konto, hensikt, desc
@reversion.create_revision()
@transaction.commit_on_success
def import_bet():
    liste = csv.reader(open(GIRO_CSV))
    liste.next()
    highest_pk = Giro.objects.all().order_by("-pk")[0].pk

    for num, rad in enumerate(liste):
        if num % 1000 == 0 and num != 0:
            transaction.commit()
            yield unicode(num)

        # Hopp over ferdig-importerte betalingar
        if int(rad[7]) < highest_pk:
            continue

        if(Giro.objects.filter(pk=rad[7]).exists()):
            continue

        g = Giro(pk=rad[7], hensikt='P')

        # Finn andsvarleg medlem
        try:
            g.medlem = Medlem.objects.alle().get(pk=rad[0])
        except Medlem.DoesNotExist:
            continue

        # Kva konto
        if rad[2].upper() in ('M', 'K', 'B'):
            g.konto = rad[2].upper()
        elif rad[1].upper() == 'L':
            # Livstidsmedlem
            if not g.medlem.status == 'L':
                g.medlem.status = 'L'
                g.medlem.save()
            continue
        elif rad[6].isdigit():
            # Viss det er pengar gjeng me ut i frå at det er snakk om kasse
            g.konto = 'K'
        else:
            print "kjenner ikkje att konto", rad, g.medlem
            continue

        # Kor mykje pengar inn?
        try:
            g.belop = float(rad[6])
        except ValueError:
            g.belop = 0
            print "belop=0", rad, g.medlem

        if len(rad[4]) > 3:
            g.innbetalt = parse(rad[4])
        try:
            g.oppretta = datetime.datetime(int(rad[5]), 1, 1, 0, 0)
        except ValueError:
            g.oppretta = g.innbetalt

        if rad[3] != "MEDLEMSKONTO":
            g.desc = rad[3]

        g.save()

def fiks_tilskipingar():
    tilskipingar = Tilskiping.objects.all()

    for tils in tilskipingar:
        medlemar = Medlem.objects.filter( \
                Q(merknad__icontains=tils.slug))
        tils.medlem_set.add(*medlemar)
        tils.save()

from django.core.mail import EmailMultiAlternatives
from django.template import Context, loader
from django.db.models import Q
import smtplib


def send_epostar():
    for overvak in LokallagOvervaking.objects.filter( Q(deaktivert__isnull=True) | Q(deaktivert__gt=datetime.datetime.now()) ):
        epost = overvak.epost
        if overvak.medlem:
            epost = overvak.medlem.epost

        sist_oppdatering = datetime.datetime.now() - datetime.timedelta(days=1)
        medlem = overvak.lokallag.medlem_set.alle().filter(oppdatert__gt=sist_oppdatering)
        nye_medlem = list(medlem.filter(oppretta__gt=sist_oppdatering).exclude(status='I'))
        nye_infofolk = list(medlem.filter(oppretta__gt=sist_oppdatering, status='I'))
        # Alle andre, "gamle" medlemar
        medlem = medlem.exclude(oppretta__gt=sist_oppdatering)

        # Finn dei som har endra lokallag
        flytta_medlem, mista_medlem, endra_medlem = [], [], []
        for m in medlem:
            old = reversion.get_for_date(m, sist_oppdatering)
            new = reversion.get_for_object(m)[0]

            changed_keys = filter(lambda k: old.field_dict[k] != new.field_dict[k], new.field_dict.keys())
            m.changed = [ (k, old.field_dict[k], new.field_dict[k]) for k in changed_keys ]
            print m, m.changed

            if 'lokallag' in changed_keys:
                flytta_medlem.append(m)
            elif 'utmeldt_dato' in changed_keys and new['utmeldt_dato']:
                mista_medlem.append(m)
            elif 'status' in changed_keys and old['status'] == 'I':
                nye_medlem.append(m)
            else:
                endra_medlem.append(m)

        dagar = (datetime.datetime.now() - sist_oppdatering).days

        # Have to use real context?
        context = Context({
                    'epost' : epost,
               'overvaking' : overvak,
                 'lokallag' : overvak.lokallag,
         'sist_oppdatering' : sist_oppdatering,
                    'dagar' : dagar,
               'nye_medlem' : nye_medlem,
             'nye_infofolk' : nye_infofolk,
            'flytta_medlem' : flytta_medlem,
             'endra_medlem' : endra_medlem,
             'mista_medlem' : mista_medlem,
             })

        text_content = loader.get_template('epostar/lokallag_overvaking.txt').render(context)
        html_content = loader.get_template('epostar/lokallag_overvaking.html').render(context)

        msg = EmailMultiAlternatives('Lokallag endra', text_content, "skriv@nynorsk.no", [epost])
        msg.attach_alternative(html_content, "text/html")
        try:
            msg.send()
        except smtplib.SMTPRecipientsRefused:
            # TODO Do logging
            pass

    return "Ferdig"
