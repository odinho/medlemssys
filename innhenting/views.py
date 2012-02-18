# -*- coding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from dateutil.parser import parse
import datetime
#from django.shortcuts import render_to_response

from medlemssys.settings import PROJECT_ROOT
from medlemssys.medlem.models import Medlem, Lokallag, Giro, Tilskiping
import csv


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
            yield "Lag: %s\n" % unicode(i)

        for i in import_medlem():
            yield "Medlem: %s\n" % unicode(i)

        for i in import_bet():
            yield "Betaling: %s\n" % unicode(i)

        fiks_tilskipingar()

    return HttpResponse(do_work(), content_type="text/plain; charset=utf-8")

@transaction.commit_on_success
def import_medlem():
    liste = csv.reader(open(PROJECT_ROOT + "/../nmudb/nmu-medl.csv.new"))
    mapping = nmu_mapping(headers=liste.next())

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
            tmp['postnr'] = int(tmp['postnr'])
        except ValueError:
            del tmp['postnr']

        if len(tmp.get('status', '')) > 1:
            #print "%s(%s) status too long: %s" % (tmp['id'], tmp['fornamn'], tmp['status'])
            tmp['status'] = tmp['status'][0]

        if len(tmp.get('kjon', '')) > 1:
            #print "%s(%s) kjon too long: %s" % (tmp['id'], tmp['fornamn'], tmp['kjon'])
            tmp['kjon'] = tmp['kjon'][0]

        tmp['innmeldt_dato'] = parse(tmp['innmeldt_dato'],
                default=datetime.datetime(1980, 1, 1, 0, 0))
        if len(tmp['utmeldt_dato']) > 2:
            tmp['utmeldt_dato'] = parse(tmp['utmeldt_dato'], default=None)
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
@transaction.commit_on_success
def import_lag():
    liste = csv.reader(open(PROJECT_ROOT + "/../nmudb/nmu-lag.csv.new"))
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
@transaction.commit_on_success
def import_bet():
    liste = csv.reader(open(PROJECT_ROOT + "/../nmudb/nmu-bet.csv.new"))
    liste.next()

    for num, rad in enumerate(liste):
        if num % 1000 == 0 and num != 0:
            transaction.commit()
            yield unicode(num)

        if(Giro.objects.filter(pk=rad[7]).exists()):
            continue

        g = Giro(pk=rad[7], hensikt='P')

        # Finn andsvarleg medlem
        try:
            g.medlem = Medlem.objects.get(pk=rad[0])
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
