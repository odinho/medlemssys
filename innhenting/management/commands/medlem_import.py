#!/usr/bin/env python
# vim: fileencoding=utf-8 shiftwidth=4 tabstop=4 expandtab softtabstop=4 ai
from __future__ import print_function
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
import os

from medlemssys.statistikk.views import update_lokallagstat

obj = ""

class Command(BaseCommand):
    args = '[ lokallag.csv [ medlem.csv [ betaling.csv ] ] ]'
    help = 'Importerer medlemane inn i databasen'
    force_update = False
    option_list = BaseCommand.option_list + (
        make_option('-f', '--force-update',
            action='store_true',
            dest='force_update',
            default=False,
            help='Tving gjennom oppdatering av giroar'),
        )

    def handle(self, *args, **options):
        global obj
        obj = self
        if options['force_update']:
            self.force_update = True

        lag_csv = self.get_filename(args, 0, 'LAG_CSV', 'nmu-lag.csv')
        medlem_csv = self.get_filename(args, 1, 'MEDLEM_CSV', 'nmu-medl.csv')
        bet_csv = self.get_filename(args, 2, 'GIRO_CSV', 'nmu-bet.csv')

        for i in import_lag(lag_csv).values():
            self.stdout.write(u"Lag: {0}\n".format(unicode(i)).encode('utf8'))

        for i in import_medlem(medlem_csv):
            self.stdout.write(u"Medlem: {0}\n".format(unicode(i)).encode('utf8'))

        for i in import_bet(bet_csv):
            self.stdout.write(u"Betaling: {0}\n".format(unicode(i)).encode('utf8'))

        fiks_tilskipingar()
        update_denormalized_fields()
        update_lokallagstat()
        send_epostar()

    def get_filename(self, args, num, setting, fallback):
        if len(args) > num:
            fn = args[0]
        else:
            fn = getattr(settings, setting, fallback)
        if not os.path.isfile(fn):
            raise CommandError("Fila finst ikkje ({0})".format(fn).encode('utf8'))
        return fn


from django.db import transaction
from django.db.models import Q
from dateutil.parser import parse
import reversion
import datetime
import csv
import re

from medlemssys.medlem.models import Medlem, Lokallag, Giro, Tilskiping, LokallagOvervaking
from medlemssys.medlem.models import KONTI, update_denormalized_fields
from medlemssys.medlem import admin # Needed to register reversion
from medlemssys.statistikk.models import LokallagStat

def stderr(msg):
    obj.stderr.write((unicode(msg) + "\n").encode('utf-8'))

RE_MEDLNR = re.compile(r'\[(\d+)\]')

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


#@reversion.create_revision() XXX There's a bug here somewhere
@transaction.commit_on_success
def import_medlem(medlem_csv_fil):
    liste = csv.reader(open(medlem_csv_fil))
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
                tmp['fodt'] = None

            try:
                tmp['postnr'] = format(int(tmp['postnr']), "04d")
            except ValueError:
                tmp['postnr'] = "9999"

            if len(tmp.get('status', '')) > 1:
                stderr(u"%s(%s) status too long: %s" % (tmp['id'], tmp['fornamn'], tmp['status']))
                tmp['status'] = tmp['status'][0].upper()

            if len(tmp.get('kjon', '')) > 1:
                stderr(u"%s(%s) kjon too long: %s" % (tmp['id'], tmp['fornamn'], tmp['kjon']))
                tmp['kjon'] = tmp['kjon'][0].upper()

            tmp['oppretta'] = parse(tmp['innmeldt_dato'],
                    default=datetime.datetime(1800, 1, 1, 0, 0))
            tmp['innmeldt_dato'] = tmp['oppretta'].date()
            tmp['oppdatert'] = datetime.datetime.now()

            if len(tmp['utmeldt_dato']) > 2:
                a = tmp['utmeldt_dato']
                tmp['utmeldt_dato'] = parse(tmp['utmeldt_dato'], default=None)
                if hasattr(tmp['utmeldt_dato'], 'date'):
                    tmp['utmeldt_dato'] = tmp['utmeldt_dato'].date()
                else:
                    stderr(u"%s(%s) utmeldt er null: %s -- org: %s" % (tmp['id'], tmp['fornamn'], tmp['utmeldt_dato'], a))
            else:
                tmp['utmeldt_dato'] = None

            # Sjekk etter [<medlemsnummer>] frå verveinfo
            if tmp['innmeldingsdetalj']:
                m = RE_MEDLNR.search(tmp['innmeldingsdetalj'])
                if m:
                    tmp['verva_av_id'] = m.group(1)
                    tmp['innmeldingstype'] = 'D'
                elif any([x for x in ["Heimesida", "heimesida", "heimeside", "Heimeside", "heimesidene", "nettskjema"] if x in tmp['innmeldingsdetalj']]):
                    tmp['innmeldingstype'] = 'H'
                elif any([x for x in [u"Målferd", u"målferd", "MF", u"målfer"] if x in tmp['innmeldingsdetalj']]):
                    tmp['innmeldingstype'] = 'M'
                elif any([x for x in ["Flygeblad", "flygeblad", "flygis", "flogskrift", "Flogskrift", "Opprop", "opprop"] if x in tmp['innmeldingsdetalj']]):
                    tmp['innmeldingstype'] = 'F'
                elif any([x for x in ["SMS", "sms"] if x in tmp['innmeldingsdetalj']]):
                    tmp['innmeldingstype'] = 'S'
                elif any([x for x in ["Lagsskiping", "lagsskiping", u"årsmøte", u"Årsmøte"] if x in tmp['innmeldingsdetalj']]):
                    tmp['innmeldingstype'] = 'L'
                elif any([x for x in ["Vitjing", "leir", "Leir"] if x in tmp['innmeldingsdetalj']]):
                    tmp['innmeldingstype'] = 'O'
                elif any([x for x in ["Telefon", "telefon", "tlf"] if x in tmp['innmeldingsdetalj']]):
                    tmp['innmeldingstype'] = 'A'

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
@reversion.create_revision()
def import_lag(lag_csv_fil):
    reversion.set_comment("Import frå Access")
    liste = csv.reader(open(lag_csv_fil))
    liste.next()
    alle_lag = {}

    for rad in liste:
        namn = rad[2].decode('utf-8')       \
                .title()                    \
                .replace(' Og ', ' og ')    \
                .replace(' I ', ' i ')      \
                .replace(u' På ', u' på ')  \
                .replace('Fmu', 'FMU')      \
                .replace('Nmu', 'NMU')      \
                .replace(' Mu', ' MU')

        lag = Lokallag(pk=rad[3],
                namn=namn,
                fylkeslag=rad[1].decode('utf-8'), distrikt=rad[0].decode('utf-8'),
                andsvar=rad[4].decode('utf-8'))
        lag.save()

        alle_lag[rad[3]] = lag

    return alle_lag

# csv: 0:MEDLNR, 1:BETALT, 2:KONTO, 3:KONTONAMN, 4;DATO, 5:AR, 6:SUM, 7:BETID
# model (giro): medlem, belop, kid, oppretta, innbetalt, konto, hensikt, desc
@transaction.commit_on_success
@reversion.create_revision()
def import_bet(bet_csv_fil):
    liste = csv.reader(open(bet_csv_fil))
    liste.next()
    try:
        highest_pk = Giro.objects.all().order_by("-pk")[0].pk
    except:
        highest_pk = -1

    for num, rad in enumerate(liste):
        if num % 1000 == 0 and num != 0:
            transaction.commit()
            yield unicode(num)

        # Hopp over ferdig-importerte betalingar
        if not obj.force_update and int(rad[7]) < highest_pk:
            continue

        if not obj.force_update and Giro.objects.filter(pk=rad[7]).exists():
            continue

        g = Giro(pk=rad[7], hensikt='P')

        # Finn andsvarleg medlem
        try:
            g.medlem = Medlem.objects.alle().get(pk=rad[0])
        except Medlem.DoesNotExist:
            stderr(u"Fann ikkje medlem %s. %s " % (rad[0], rad))
            continue

        # Kva konto
        if rad[2].upper() in [ k[0] for k in KONTI ]:
            g.konto = rad[2].upper()
        elif rad[1].upper() == 'L':
            # Livstidsmedlem
            if not g.medlem.status == 'L':
                g.medlem.status = 'L'
                g.medlem.save()
                stderr(u"Oppdaterte %s til L. %s " % (g.medlem, rad))
            stderr(u"Hopper over %s (L). %s " % (g.medlem, rad))
            continue
        elif rad[6].isdigit():
            # Viss det er pengar gjeng me ut i frå at det er snakk om kasse
            g.konto = 'K'
            stderr(u"Gjettar at pengar (%s) er til KASSE %s -- %s" % (rad[6], g.medlem, rad))
        else:
            stderr(u"Kjenner ikkje att konto: {0}, {1}".format(g.medlem, rad))
            continue

        # Kor mykje pengar inn?
        try:
            g.belop = float(rad[6])
        except ValueError:
            g.belop = 0
            stderr(u"Beløp = 0: {0}, {1}".format(g.medlem, rad))

        if len(rad[4]) > 3:
            g.innbetalt = parse(rad[4])
        else:
            stderr(u"Ikkje innbetalt! {0}, {1}".format(g.medlem, rad))

        try:
            g.oppretta = datetime.datetime(int(rad[5]), 1, 1, 0, 0)
        except ValueError:
            stderr(u"Gjettar oppretta==innbetalt: {0}, {1}".format(g.medlem, rad))
            g.oppretta = g.innbetalt

        if rad[3] != "MEDLEMSKONTO":
            g.desc = rad[3]

        g.save()

        if num < 99:
            yield unicode(g)


def fiks_tilskipingar():
    tilskipingar = Tilskiping.objects.all()

    for tils in tilskipingar:
        medlemar = Medlem.objects.filter( \
                Q(merknad__icontains=tils.slug))
        tils.medlem_set.add(*medlemar)
        tils.save()

from django.core.mail import EmailMultiAlternatives
from django.template import Context, loader
import smtplib, json

def send_epostar():
    for overvak in LokallagOvervaking.objects.filter( Q(deaktivert__isnull=True) | Q(deaktivert__gt=datetime.datetime.now()) ):
        epost = overvak.epost
        if overvak.medlem:
            epost = overvak.medlem.epost

        if (datetime.datetime.now() - overvak.sist_oppdatert) > datetime.timedelta(days=6, seconds=22*60*60):
            # Har sendt epost for mindre enn 7 dagar sidan, so ikkje send noko no.
            # TODO: Dette er ein sjukt dårleg måte å gjera dette på, fiks betre
            continue

        sist_oppdatering = overvak.sist_oppdatert

        medlem = overvak.lokallag.medlem_set.alle().filter(oppdatert__gt=sist_oppdatering)
        nye_medlem = list(medlem.filter(oppretta__gt=sist_oppdatering).exclude(status='I'))
        nye_infofolk = list(medlem.filter(oppretta__gt=sist_oppdatering, status='I'))
        # Alle andre, "gamle" medlemar
        medlem = medlem.exclude(oppretta__gt=sist_oppdatering)

        # Finn dei som har flytta til eit ANNA lokallag
        try:
            medlemar_sist = LokallagStat.objects                \
                .get(                                           \
                    veke="{0:%Y-%W}".format(sist_oppdatering),  \
                    lokallag=overvak.lokallag                   \
                ).interessante
            medlemar_sist = json.loads(medlemar_sist)
        except LokallagStat.DoesNotExist:
            stderr(u"LokallagStat for {0}, {1:%Y-%W} fanst ikkje.".format(overvak.lokallag, sist_oppdatering))
            vekkflytta_medlem = []
        else:
            medlemar_no = overvak.lokallag.medlem_set.interessante().values_list('pk', flat=True)
            vekkflytta_medlem = Medlem.objects.filter(pk__in=set(medlemar_sist) - set(medlemar_no))


        flytta_medlem, utmeld_medlem, endra_medlem = [], [], []
        for m in medlem:
            old = reversion.get_for_date(m, sist_oppdatering)
            new = reversion.get_for_object(m)[0]

            changed_keys = filter(lambda k: old.field_dict[k] != new.field_dict[k], new.field_dict.keys())
            m.changed = [ (k, old.field_dict[k], new.field_dict[k]) for k in changed_keys ]

            if 'lokallag' in changed_keys:
                flytta_medlem.append(m)
            elif 'utmeldt_dato' in changed_keys and new['utmeldt_dato']:
                utmeld_medlem.append(m)
            elif 'status' in changed_keys and old['status'] == 'I':
                nye_medlem.append(m)
            else:
                endra_medlem.append(m)

        dagar = (datetime.datetime.now() - sist_oppdatering).days

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
            'utmeld_medlem' : utmeld_medlem,
        'vekkflytta_medlem' : vekkflytta_medlem,
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
