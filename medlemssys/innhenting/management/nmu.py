# -*- encoding: utf-8 -*-

# -*- coding: utf-8 -*-
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
from __future__ import unicode_literals

import csv
import datetime
import logging
import re
import sys
import textwrap

from dateutil.parser import parse
from django.db import transaction
from reversion import revisions as reversion

from medlemssys.medlem.models import KONTI
from medlemssys.medlem.models import Medlem, Lokallag, Giro


logger = logging.getLogger(__name__)

class AccessImporter(object):
    # REGISTERKODE,LAGSNR,MEDLNR,FORNAMN,MELLOMNAMN,ETTERNAMN,TILSKRIFT1,TILSKRIFT2,POST,VERVA,VERV,LP,GJER,MERKNAD,FØDEÅR,KJØNN,INN,INNMEDL,UTB,UT_DATO,MI,MEDLEMINF,TLF_H,TLF_A,E_POST,H_TILSKR1,H_TILSKR2,H_POST,H_TLF,Ring_B,Post_B,Epost_B,MM_B,MNM_B,BRUKHEIME,FARRETOR,RETUR,REGBET,HEIMEADR,REGISTRERT,TILSKRIFT_ENDRA
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

    @transaction.atomic
    def import_medlem(self, medlem_fn):
        with reversion.create_revision():
            reversion.set_comment(u"CSV import")
            for num, [medlem_dict, raw_data] in enumerate(
                    self._get_medlem(medlem_fn)):
                if not self.clean_medlem_dict(medlem_dict, raw_data):
                    continue
                val = medlem_dict.get('_val', [])
                tmp = dict((k, medlem_dict[k]) for k in medlem_dict if not k.startswith('_'))
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
            logger.warning(u"%s(%s) ugyldig medlemsnummer! Ignorerer medlemen." % (medlem['id'], medlem['fornamn']))
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
            logger.warning(u"%s(%s) forstår ikkje postnr: %s" % (medlem['id'], medlem['fornamn'], medlem['postnr']))
            medlem['postnr'] = "9999"

        if len(medlem.get('status', '')) > 1:
            logger.warning(u"%s(%s) status too long: %s" % (medlem['id'], medlem['fornamn'], medlem['status']))
            medlem['status'] = medlem['status'][0].upper()

        if len(medlem.get('kjon', '')) > 1:
            logger.warning(u"%s(%s) kjon too long: %s" % (medlem['id'], medlem['fornamn'], medlem['kjon']))
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
                logger.warning(u"%s(%s) utmeldt er null: %s -- org: %s" % (medlem['id'], medlem['fornamn'], medlem['utmeldt_dato'], a))
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


    def _get_medlem(self, medlem_fn):
        liste = csv.reader(open(medlem_fn))
        mapping = self._create_mapping(headers=liste.next())
        if not mapping:
            logger.error(u"%s: ser ikkje ut som ein medlems-csv fil (manglar header?)" % self.medlem_fil)
            sys.exit()
        for rad in liste:
            tmp = {}
            for typ in self.CSV_MAP.values():
                if typ not in mapping:
                    logger.warning(u"Type '" + unicode(typ) + u"' not in mapping. row = " + unicode(rad))
                tmp[typ] = rad[mapping[typ]] \
                            .decode("utf-8") \
                            .replace(r"\n", "\n")
            yield tmp, rad


    def _create_mapping(self, headers):
        mapping = dict()
        for h in self.CSV_MAP.keys():
            if h in headers:
                mapping[self.CSV_MAP[h]] = headers.index(h)
            else:
                raise Exception("Fann ikkje {0} som header.".format(h))
        return mapping


    # csv: DIST,FLAG,LLAG,lid,ANDSVAR,LOKALSATS
    # model: namn, fylkeslag, distrikt, andsvar
    @transaction.atomic
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
                lag.andsvar = rad[4].decode('utf-8')
            else:
                lag = Lokallag(pk=rad[3], namn=namn, andsvar=rad[4].decode('utf-8'))
            lag.save()

            alle_lag[rad[3]] = lag

        return alle_lag

    # csv: 0:MEDLNR, 1:BETALT, 2:KONTO, 3:KONTONAMN, 4;DATO, 5:AR, 6:SUM, 7:BETID
    # model (giro): medlem, belop, kid, oppretta, innbetalt, konto, hensikt, desc
    @transaction.atomic
    @reversion.create_revision()
    def import_bet(self, force_update):
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
            if not force_update and int(rad[7]) < highest_pk:
                continue

            if not force_update and Giro.objects.filter(pk=rad[7]).exists():
                continue

            g = Giro(pk=rad[7], hensikt='P', status='F')

            # Finn andsvarleg medlem
            try:
                g.medlem = Medlem.objects.alle().get(pk=rad[0])
            except Medlem.DoesNotExist:
                logger.warning(u"Fann ikkje medlem %s. %s " % (rad[0], rad))
                continue

            # Kva konto
            if rad[2].upper() in [ k[0] for k in KONTI ]:
                g.konto = rad[2].upper()
            elif rad[1].upper() == 'L':
                # Livstidsmedlem
                if not g.medlem.status == 'L':
                    g.medlem.status = 'L'
                    g.medlem.save()
                    logger.warning(u"Oppdaterte %s til L. %s " % (g.medlem, rad))
                logger.warning(u"Hopper over %s (L). %s " % (g.medlem, rad))
                continue
            elif rad[6].isdigit():
                # Viss det er pengar gjeng me ut i frå at det er snakk om kasse
                g.konto = 'K'
                logger.warning(u"Gjettar at pengar (%s) er til KASSE %s -- %s" % (rad[6], g.medlem, rad))
            else:
                logger.warning(u"Kjenner ikkje att konto: {0}, {1}".format(g.medlem, rad))
                continue

            # Kor mykje pengar inn?
            try:
                g.belop = float(rad[6])
            except ValueError:
                g.belop = 0
                logger.warning(u"Beløp = 0: {0}, {1}".format(g.medlem, rad))

            if len(rad[4]) > 3:
                g.innbetalt = parse(rad[4])
                g.innbetalt_belop = g.belop
            else:
                logger.warning(u"Ikkje innbetalt! {0}, {1}".format(g.medlem, rad))

            try:
                g.oppretta = datetime.datetime(int(rad[5]), 1, 1, 0, 0)
            except ValueError:
                logger.warning(u"Gjettar oppretta==innbetalt: {0}, {1}".format(g.medlem, rad))
                g.oppretta = g.innbetalt

            g.gjeldande_aar = g.oppretta.year

            if rad[3] != "MEDLEMSKONTO":
                g.desc = rad[3]

            g.save()

            if num < 99:
                yield unicode(g)

class MamutImporter(AccessImporter):
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
            logger.error(u"%s(%s) ugyldig medlemsnummer! Ignorerer medlemen." % (medlem['id'], medlem['fornamn']))
            return False
        if medlem['_is_customer'] != "SANN":
            logger.info(u"%s(%s) ikkje customer. Ignorerer medlemen." % (medlem['id'], medlem['fornamn']))
            return False

        namn = medlem['fornamn'].split()
        if len(namn) > 1:
            medlem['fornamn'] = " ".join(namn[:-1])
            medlem['etternamn'] = namn[-1]
        else:
            medlem['etternamn'] = '-'

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
                raise Exception("wat! nutin: " + unicode(grupper))
            medlem['utmeldt_dato'] = datetime.date(int(sagtopp.group(1)), 1, 1)
            grupper.remove('Sagt opp ' + sagtopp.group(1))

        if any(k in medlem['_gruppe'].lower()
               for k in ('utmeldt', 'fjerna', 'sagt opp')):
            if 'utmeldt_dato' not in medlem:
                logger.info(u"%s(%s) utmeldt, men aktiv. gruppe:%s." % (medlem['id'], medlem['fornamn'], medlem['_gruppe'][:-1]))
        elif ('utmeldt_dato' in medlem and
                any(k in medlem['_gruppe'].lower() for k in ('tingar'))):
            logger.error(u"%s(%s %s) FEILUTMELDING. gruppe:%s." % (medlem['id'], medlem['fornamn'], medlem['etternamn'], medlem['_gruppe'][:-1]))
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

class GuessingCSVImporter(AccessImporter):
    MATCH_LOOKUP = {
      'id': ['pk', 'nr', 'medlemsnr', 'medlnr', 'medlid', 'medlemsid',
             'mid', 'mnr', 'nummer'],
      'fornamn': ['fornavn', 'firstname', 'namn', 'navn'],
      'mellomnamn': ['mellomnavn', 'middlename'],
      'etternamn': ['etternavn', 'lastname'],
      'fodt': ['født', 'år', 'born', 'year', 'fødeår'],
      'postnr': ['postnummer', 'zip', 'zipcode', 'post'],
      'epost': ['e-post', 'email'],
      'postadr': ['postadresse', 'postadresse1', 'heimetilskrift',
                  'heimeadresse', 'hjemmeadresse', 'heaimeadr', 'hjemmeadr',
                  'htilskrift', 'hadresse', 'htilskr', 'gateadresse',
                  'gateadresse1', 'addresse', 'tilskrift', 'tilskr', 'adr'],
      'mobnr': ['mobil', 'tlfmobil', 'tlfnr', 'mobilnummer', 'telefonnummer'],
      'merknad': ['notat', 'kommentar', 'notes', 'comment', 'extra', 'ekstra'],
      'kjon': ['kjøn', 'kjønn', 'kjonn', 'sex'],
      'gjer': ['gjør', 'workplace', 'what'],
      'innmeldt_dato': ['innmeldttid', 'innmeldt'],
      'utmeldt_dato': ['utmeldttid', 'utmeldt', 'utdato', 'datout'],
      'oppretta': ['created', 'creationdate', 'creationtime',],
      'oppdatert': ['updated', 'updatedate', 'lastupdated', 'oppdaterttid', 'oppdatertdato'],
      '_lokallag': ['lokallag', 'lag', 'gruppe'],
      '_val': ['val', 'valg', 'grupper'],
      'heimenr': ['tlfheime', 'tlfhjemme', 'tlfprivat', 'privattlf'],
      'bortepostnr': [],
      'borteadr': [],
      'status': [],
      'mellomnamn': [],
    }

    REQUIRED = ['id', 'fornamn', 'fodt', 'postnr']

    def __init__(self, *args, **kwargs):
        self._matches = {v: None for v in self.REQUIRED}
        super(GuessingCSVImporter, self).__init__(*args, **kwargs)

    def _get_medlem(self, medlem_fn):
        fp = open(medlem_fn)
        dialect = csv.Sniffer().sniff(fp.read(1024), delimiters=str(';,'))
        fp.seek(0)
        reader = csv.DictReader(open(medlem_fn), dialect=dialect)
        fields = [f.decode('utf-8') for f in reader.fieldnames]
        if len(fields) < 5:
            print(textwrap.dedent("""
                Suspicously few fields: {entr}.
                Wrong delimiter?  Headers not on first line?

                Quitting.
                """).format(entr=', '.join(unicode(s) for s in fields)))
            sys.exit(1)

        self._create_mapping(fields, self._matches)
        missing_fields = (
            set(self.MATCH_LOOKUP.keys()) - set(self._matches.keys()))
        unused_fields = (
            set(fields) -
            set(f.decode('utf-8') for f in self._matches.values() if f))
        if missing_fields or unused_fields:
            print(textwrap.dedent("""
                The fields and database don't match up perfectly.

                Fields in database that's missing a mapping from CSV:
                {missing}

                Fields in CSV that's unused for a mapping to database:
                {unused}
                """).format(
                    missing='\n'.join(sorted(missing_fields)),
                    unused='\n'.join(sorted(unused_fields)))
                )
        print(textwrap.dedent("""
            The mapping between CSV and database is:
              {mapping}
            """).format(mapping = self._matches))
        missing_required = [k for k, v in self._matches.items() if not v]
        if missing_required:
            print(textwrap.dedent("""
                Some required fields are missing:
                  {}
                """).format(', '.join(missing_required)))
            sys.exit(1)
        raw_input('Ctrl+C to stop. Enter to continue.');

        for line in reader:
            tmp = {db_key: line[csv_key].decode('utf-8') for
                       db_key, csv_key in self._matches.items()}
            yield tmp, line

    def _create_mapping(self, input_keys, matches):
        def find_matches(key_normalizer):
            for original_key in input_keys:
                normalized_key = key_normalizer(original_key)
                for match_key, match_values in self.MATCH_LOOKUP.items():
                    if matches.get(match_key):
                        continue
                    for match_variation in [match_key] + match_values:
                        if normalized_key == match_variation:
                            # csv module in Python 2 is totally fucked up.
                            # It deals with bytes-as-strings and not unicode
                            # So this is messed up.
                            matches[match_key] = original_key.encode('utf-8')
                            break
        find_matches(lambda k: ''.join(k.lower().split()))
        find_matches(lambda k: re.sub(r'[^\w]', '',  k.lower()))
        find_matches(lambda k: re.sub(r'[\W\d_-]', '',  k.lower()))

    def clean_medlem_dict(self, medlem, raw_data=None):
        if not medlem['id'].isdigit():
            logger.error(u"%s(%s) ugyldig medlemsnummer! Ignorerer medlemen." %
                (medlem['id'], medlem['fornamn']))
            return False

        if 'fornamn' in medlem and not 'etternamn' in medlem:
            namn = medlem['fornamn'].split()
            if len(namn) > 1:
                medlem['fornamn'] = " ".join(namn[:-1])
                medlem['etternamn'] = namn[-1]
            else:
                medlem['etternamn'] = '-'

        try:
            medlem['fodt'] = int(medlem['fodt'])
        except ValueError:
            medlem['fodt'] = None

        if len(medlem.get('kjon', '')) > 1:
            kjon = medlem['kjon'].lower()
            if kjon in ['g', 'gutt', 'm', 'mann', 'male', 'man']:
                medlem['kjon'] = 'M'
            elif kjon in ['j', 'jente', 'k', 'kvinne', 'female', 'woman']:
                medlem['kjon'] = 'K'
            else:
                logger.warning(u"%s(%s) dunno kjon: %s" % (medlem['id'], medlem['fornamn'], medlem['kjon']))
                medlem['kjon'] = 'U'

        if (medlem['postnr'].isdigit() and
                medlem['postnr'] > '0000' and
                medlem['postnr'] < '9999'):
            medlem['ekstraadr'] = ''
        else:
            medlem['ekstraadr'] = ' '.join((medlem['postnr'],
                                            medlem.get('ekstraadr', '')))
            medlem['postnr'] = '9999'

        fake_date = datetime.datetime(1800, 1, 1, 0, 0)
        def makedate(key, fallback=fake_date):
            try:
                return parse(medlem[key], default=fallback)
            except:
                return fallback

        if not 'oppretta' in medlem:
            medlem['oppretta'] = makedate('innmeldt_dato')
        medlem['oppdatert'] =  makedate('oppdatert', datetime.datetime.now())
        medlem['innmeldt_dato'] = makedate('innmeldt_dato')
        medlem['utmeldt_dato'] =  makedate('utmeldt_dato', None)

        if medlem.get('epost'):
            if not '@' in medlem['epost']:
                medlem['merknad'] = medlem['epost']
                medlem['epost'] = ''
            if '<' in medlem['epost']:
                m = re.search(r'<([^>]+)>', medlem['epost'])
                if m and m.group(1):
                    medlem['epost'] = m.group(1)
            if ' ' in medlem['epost']:
                raise Exception("Mellomrom i epost")

        if medlem.get('mobnr'):
            medlem['mobnr'] = ''.join(medlem['mobnr'].split())
            if len(medlem['mobnr']) < 4:
                del medlem['mobnr']

        if medlem.get('_lokallag'):
            medlem['lokallag'] = Lokallag.objects.get_or_create(
                namn=medlem['_lokallag'].strip(),
                defaults={ 'fylke': '', 'kommunes': '', 'andsvar': ''})[0]

        return True
