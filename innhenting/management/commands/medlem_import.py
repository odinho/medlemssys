#!/usr/bin/env python
# vim: fileencoding=utf-8 shiftwidth=4 tabstop=4 expandtab softtabstop=4 ai
from __future__ import print_function

import os

from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from statistikk.views import update_lokallagstat, send_overvakingar

obj = ""

class Command(BaseCommand):
    args = '[ medlem.csv [ lokallag.csv [ betaling.csv ] ] ]'
    help = "Importerer medlemane inn i databasen"
    force_update = False
    option_list = BaseCommand.option_list + (
        make_option('-f', '--force-update',
            action='store_true',
            dest='force_update',
            default=False,
            help="tving gjennom oppdatering av giroar"),
        make_option('--importer',
            dest='importer',
            default='nmu_access',
            help="importeringssystem (nmu_access eller mamut)"),
        )

    def handle(self, *args, **options):
        global obj
        obj = self
        if options['force_update']:
            self.force_update = True

        medlem_csv = self.get_filename(args, 0, 'MEDLEM_CSV', 'nmu-medl.csv')
        lag_csv = self.get_filename(args, 1, 'LAG_CSV', 'nmu-lag.csv')
        bet_csv = self.get_filename(args, 2, 'GIRO_CSV', 'nmu-bet.csv')

        if options['importer'] == 'nmu_access':
            imp = NMUAccessImporter(medlem_csv, lag_csv, bet_csv)
        elif options['importer'] == 'mamut':
            imp = MamutImporter(medlem_csv, lag_csv, bet_csv)
        else:
            raise CommandError("Importeren finst ikkje ({0})".format(options['importer']).encode('utf8'))

        for i in imp.import_lag().values():
            self.stdout.write(u"Lag: {0}\n".format(unicode(i)).encode('utf8'))

        for i in imp.import_medlem():
            self.stdout.write(u"Medlem: {0}\n".format(unicode(i)).encode('utf8'))

        for i in imp.import_bet():
            self.stdout.write(u"Betaling: {0}\n".format(unicode(i)).encode('utf8'))

        update_denormalized_fields()
        update_lokallagstat()
        send_overvakingar()

    def get_filename(self, args, num, setting, fallback):
        if len(args) > num:
            fn = args[num]
        else:
            fn = getattr(settings, setting, fallback)
        if not os.path.isfile(fn):
            raise CommandError("Fila finst ikkje ({0})".format(fn).encode('utf8'))
        return fn


import csv
import datetime
import re
import sys

import reversion
from django.db import transaction
from django.db.models import Q
from dateutil.parser import parse

from medlem.models import Medlem, Lokallag, Giro
from medlem.models import KONTI, update_denormalized_fields
from statistikk.models import LokallagStat

def stderr(msg):
    if obj:
        obj.stderr.write((unicode(msg) + "\n").encode('utf-8'))
    else:
        print((unicode(msg)).encode('utf-8'))

class NMUAccessImporter(object):
    # REGISTERKODE,LAGSNR,MEDLNR,FORNAMN,MELLOMNAMN,ETTERNAMN,TILSKRIFT1,TILSKRIFT2,POST,VERVA,VERV,LP,GJER,MERKNAD,FØDEÅR,KJØNN,INN,INNMEDL,UTB,UT_DATO,MI,MEDLEMINF,TLF_H,TLF_A,E_POST,H_TILSKR1,H_TILSKR2,H_POST,H_TLF,Ring_B,Post_B,Epost_B,MM_B,MNM_B,BRUKHEIME,FARRETOR,RETUR,REGBET,HEIMEADR,REGISTRERT,TILSKRIFT_ENDRA
    # (gamal) REGISTERKODE,LAGSNR,MEDLNR,FORNAMN,MELLOMNAMN,ETTERNAMN,TILSKRIFT1,TILSKRIFT2,POST,VERVA,VERV,LP,GJER,MERKNAD,KJØNN,INN,INNMEDL,UTB,UT_DATO,MI,MEDLEMINF,TLF_H,TLF_A,E_POST,H_TILSKR1,H_TILSKR2,H_POST,H_TLF,Ring_B,Post_B,MM_B,MNM_B,BRUKHEIME,FARRETOR,RETUR,REGBET,HEIMEADR,REGISTRERT,TILSKRIFT_ENDRA,FØDEÅR,Epost_B
    CSV_MAP = {
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
            (29, 0, 'Ikkje ring'), # RING_B = 28 (old id)
            (30, 0, 'Ikkje post'), # POST_B = 29
            (31, 0, 'Ikkje epost'), # EPOST_B = 40
            (32, 0, 'Ikkje Motmæle'), # MM_B = 30
            (33, 0, 'Ikkje Norsk Tidend'), # MNM_B = 31
    )

    def __init__(self, medlem_fil, lag_fil, bet_fil):
        self.medlem_fil = medlem_fil
        self.lag_fil = lag_fil
        self.bet_fil = bet_fil

    #@reversion.create_revision() XXX There's a bug here somewhere
    @transaction.commit_on_success
    def import_medlem(self):
        liste = csv.reader(open(self.medlem_fil))
        mapping = self.create_mapping(headers=liste.next())
        if not mapping:
            stderr(u"%s: ser ikkje ut som ein medlems-csv fil (manglar header?)" % self.medlem_fil)
            sys.exit()

        with reversion.create_revision():
            reversion.set_comment("Import frå Access")

            for num, rad in enumerate(liste):
                tmp = {}
                for typ in self.CSV_MAP.values():
                    if typ not in mapping:
                        stderr(u"Type '" + unicode(typ) + u"' not in mapping. row = " + unicode(rad))
                    tmp[typ] = rad[mapping[typ]] \
                                .decode("utf-8") \
                                .replace(r"\n", "\n")
                if not self.clean_medlem_dict(tmp, raw_data=rad):
                    continue
                val = tmp['_val']
                tmp = dict((k, tmp[k]) for k in tmp if not k.startswith('_'))
                m = Medlem(**tmp)
                m.save()

                for v in val:
                    m.set_val(v)

                # Print first 200 names
                if num < 199:
                    yield u"{0:>3}. {1}".format(unicode(num), unicode(m))

                elif num%200 == 0 and num != 0:
                    transaction.commit()
                    yield unicode(num)


    re_medlnr = re.compile(r'\[(\d+)\]')
    def clean_medlem_dict(self, medlem, raw_data=None):
        '''Cleans the member dict in-place. Returns False when unprocessed.'''

        if not medlem['id'].isdigit():
            stderr(u"%s(%s) ugyldig medlemsnummer! Ignorerer medlemen." % (medlem['id'], medlem['fornamn']))
            return False

        try:
            medlem['lokallag_id'] = int(medlem['lokallag'])
        except (KeyError, ValueError):
            pass
        finally:
            del medlem['lokallag']

        try:
            medlem['fodt'] = int(medlem['fodt'])
        except ValueError:
            medlem['fodt'] = None

        try:
            medlem['postnr'] = format(int(medlem['postnr']), "04d")
        except ValueError:
            stderr(u"%s(%s) forstår ikkje postnr: %s" % (medlem['id'], medlem['fornamn'], medlem['postnr']))
            medlem['postnr'] = "9999"

        if len(medlem.get('status', '')) > 1:
            stderr(u"%s(%s) status too long: %s" % (medlem['id'], medlem['fornamn'], medlem['status']))
            medlem['status'] = medlem['status'][0].upper()

        if len(medlem.get('kjon', '')) > 1:
            stderr(u"%s(%s) kjon too long: %s" % (medlem['id'], medlem['fornamn'], medlem['kjon']))
            medlem['kjon'] = medlem['kjon'][0].upper()

        medlem['oppretta'] = parse(medlem['innmeldt_dato'],
                default=datetime.datetime(1800, 1, 1, 0, 0))
        medlem['innmeldt_dato'] = medlem['oppretta'].date()
        medlem['oppdatert'] = datetime.datetime.now()

        if len(medlem['utmeldt_dato']) > 2:
            a = medlem['utmeldt_dato']
            medlem['utmeldt_dato'] = parse(medlem['utmeldt_dato'], default=None)
            if hasattr(medlem['utmeldt_dato'], 'date'):
                medlem['utmeldt_dato'] = medlem['utmeldt_dato'].date()
            else:
                stderr(u"%s(%s) utmeldt er null: %s -- org: %s" % (medlem['id'], medlem['fornamn'], medlem['utmeldt_dato'], a))
        else:
            medlem['utmeldt_dato'] = None

        # Sjekk etter [<medlemsnummer>] frå verveinfo
        if medlem['innmeldingsdetalj']:
            m = self.re_medlnr.search(medlem['innmeldingsdetalj'])
            if m:
                medlem['verva_av_id'] = m.group(1)
                medlem['innmeldingstype'] = 'D'
            elif any([x for x in ["Heimesida", "heimesida", "heimeside", "Heimeside", "heimesidene", "nettskjema"] if x in medlem['innmeldingsdetalj']]):
                medlem['innmeldingstype'] = 'H'
            elif any([x for x in [u"Målferd", u"målferd", "MF", u"målfer"] if x in medlem['innmeldingsdetalj']]):
                medlem['innmeldingstype'] = 'M'
            elif any([x for x in ["Flygeblad", "flygeblad", "flygis", "flogskrift", "Flogskrift", "Opprop", "opprop"] if x in medlem['innmeldingsdetalj']]):
                medlem['innmeldingstype'] = 'F'
            elif any([x for x in ["SMS", "sms"] if x in medlem['innmeldingsdetalj']]):
                medlem['innmeldingstype'] = 'S'
            elif any([x for x in ["Lagsskiping", "lagsskiping", u"årsmøte", u"Årsmøte"] if x in medlem['innmeldingsdetalj']]):
                medlem['innmeldingstype'] = 'L'
            elif any([x for x in ["Vitjing", "leir", "Leir"] if x in medlem['innmeldingsdetalj']]):
                medlem['innmeldingstype'] = 'O'
            elif any([x for x in ["Telefon", "telefon", "tlf"] if x in medlem['innmeldingsdetalj']]):
                medlem['innmeldingstype'] = 'A'

        medlem['_val'] = []
        for v in self.VAL:
            if raw_data[v[0]] != "" and int(raw_data[v[0]]) == int(v[1]):
                medlem['_val'].append(v[2])

        return True



    def create_mapping(self, headers):
        mapping = dict()
        for h in self.CSV_MAP.keys():
            if h in headers:
                mapping[self.CSV_MAP[h]] = headers.index(h)
            else:
                raise Exception("Fann ikkje {0} som header.".format(h))
        return mapping

    # csv: DIST,FLAG,LLAG,lid,ANDSVAR,LOKALSATS
    # model: namn, fylkeslag, distrikt, andsvar
    @transaction.commit_on_success
    @reversion.create_revision()
    def import_lag(self):
        reversion.set_comment("Import frå Access")
        liste = csv.reader(open(self.lag_fil))
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

            lag = Lokallag.objects.filter(pk=rad[3])
            if len(lag):
                lag = lag[0]
                lag.namn = namn
                lag.fylkeslag = rad[1].decode('utf-8')
                lag.distrikt = rad[0].decode('utf-8')
                lag.andsvar = rad[4].decode('utf-8')
            else:
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
    def import_bet(self):
        liste = csv.reader(open(self.bet_fil))
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

            g = Giro(pk=rad[7], hensikt='P', status='F')

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
                g.innbetalt_belop = g.belop
            else:
                stderr(u"Ikkje innbetalt! {0}, {1}".format(g.medlem, rad))

            try:
                g.oppretta = datetime.datetime(int(rad[5]), 1, 1, 0, 0)
            except ValueError:
                stderr(u"Gjettar oppretta==innbetalt: {0}, {1}".format(g.medlem, rad))
                g.oppretta = g.innbetalt

            g.gjeldande_aar = g.oppretta.year

            if rad[3] != "MEDLEMSKONTO":
                g.desc = rad[3]

            g.save()

            if num < 99:
                yield unicode(g)

class MamutImporter(NMUAccessImporter):
    CSV_MAP = {
            'cont': '_is_customer',
            'contid': 'id',
            'name': 'fornamn',
            'zipcode': 'postnr',
            'street': 'postadr',
            'city': 'ekstraadr',
            'regdate': 'innmeldt_dato',
            'editdate': 'oppdatert',
            'active': '_active',
            'email': 'epost',
            'phone1': 'mobnr',
            'gruppe': '_gruppe',
        }

    def clean_medlem_dict(self, medlem, raw_data=None):
        if not medlem['id'].isdigit():
            stderr(u"%s(%s) ugyldig medlemsnummer! Ignorerer medlemen." % (medlem['id'], medlem['fornamn']))
            return False
        if medlem['_is_customer'] != "SANN":
            stderr(u"%s(%s) ikkje customer. Ignorerer medlemen." % (medlem['id'], medlem['fornamn']))
            return False

        namn = medlem['fornamn'].split()
        if len(namn) > 1:
            medlem['fornamn'] = " ".join(namn[:-1])
            medlem['etternamn'] = namn[-1]
        else:
            medlem['etternamn'] = '-'

        if (medlem['postnr'].isdigit() and
                medlem['postnr'] > '0000' and
                medlem['postnr'] < '9999'):
            medlem['ekstraadr'] = ''
        else:
            medlem['ekstraadr'] = ' '.join((medlem['postnr'],
                                            medlem['ekstraadr']))
            medlem['postnr'] = '9999'

        medlem['oppretta'] = parse(medlem['innmeldt_dato'],
                default=datetime.datetime(1800, 1, 1, 0, 0))
        medlem['innmeldt_dato'] = medlem['oppretta'].date()
        medlem['oppdatert'] = parse(medlem['oppdatert'],
                default=datetime.datetime(1800, 1, 1, 0, 0))


        if not '@' in medlem['epost']:
            medlem['merknad'] = medlem['epost']
            medlem['epost'] = ''
        elif ' ' in medlem['epost']:
            raise Exception("Mellomrom i epost")

        if medlem['mobnr']:
            medlem['mobnr'] = ''.join(medlem['mobnr'].split())
            if len(medlem['mobnr']) < 4:
                del medlem['mobnr']

        grupper = medlem['_gruppe'].splitlines()
        if medlem['_active'] != "SANN":
            medlem['utmeldt_dato'] = medlem['oppdatert'].date()
        elif 'sagt opp' in medlem['_gruppe'].lower():
            sagtopp = next((re.match('Sagt opp (\d+)', x)
                           for x in grupper if 'Sagt opp' in x))
            if not sagtopp:
                raise Exception("wat! nutin: " + str(grupper))
            medlem['utmeldt_dato'] = datetime.date(int(sagtopp.group(1)), 1, 1)
            grupper.remove('Sagt opp ' + sagtopp.group(1))

        if any(k in medlem['_gruppe'].lower()
               for k in ('utmeldt', 'fjerna', 'sagt opp')):
            if 'utmeldt_dato' not in medlem:
                stderr(u"%s(%s) utmeldt, men aktiv. gruppe:%s." % (medlem['id'], medlem['fornamn'], medlem['_gruppe'][:-1]))
        elif ('utmeldt_dato' in medlem and
                any(k in medlem['_gruppe'].lower() for k in ('tingar'))):
            stderr(u"%s(%s %s) FEILUTMELDING. gruppe:%s." % (medlem['id'], medlem['fornamn'], medlem['etternamn'], medlem['_gruppe'][:-1]))
            #raise Exception("utmeldt utan å vera det.")

        lokallag=None
        for g in grupper:
            if g.startswith('Tingar:') or g.startswith('Gruppetingarar:'):
                lokallag = g
                grupper.remove(lokallag)
                break
        # Gjer resterande til val
        medlem['_val'] = grupper

        if lokallag:
            medlem['lokallag'] = Lokallag.objects.get_or_create(
                namn=lokallag.strip(),
                defaults={ 'fylkeslag': '', 'distrikt': '', 'andsvar': ''})[0]

        return True
