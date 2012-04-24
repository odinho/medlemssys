#!/usr/bin/env python
# vim: fileencoding=utf-8 shiftwidth=4 tabstop=4 expandtab softtabstop=4 ai
from __future__ import print_function
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
import os
from ocr import parse_ocr

obj = ""

class Command(BaseCommand):
    args = '[ ocr_fil.txt ]'
    help = 'Registrerer OCR-innbetalingar'

    def handle(self, *args, **options):
        if len(args):
            fn = args[0]
        else:
            fn = getattr(settings, 'OCR_FIL', 'ocr.txt')

        if not os.path.isfile(fn):
            raise CommandError("Fila finst ikkje ({0})".format(fn).encode('utf8'))

        ocr_file = open(fn)
        ocr = parse_ocr(ocr_file)

        for f in ocr:
            try:
                giro = Giro.objects.get(
                        Q(oppretta__year=f['dato'].year) | Q(oppretta__year=(f['dato'].year - 1)),
                        kid=f['kid'],
                    )
            except Giro.DoesNotExist:
                self.stderr.write("Fann ikkje giroen, {dato:6s} {belop:4n} {kid:12s} {transaksjon}\n".format(**f))
                continue

            if f['belop'] < giro.belop:
                self.stderr("{giro}: for lite betalt! Rekna {giro.belop}, fekk {f.belop} ({giro.pk})".format(giro=giro, f=f))
                self.stderr("FARE, lagrar ikkje denne her. Tenk ut noko lurt...")
                # XXX: Kva skal eg gjera her?
                continue
            elif f['belop'] > giro.belop:
                self.stderr("{giro}: Betalte meir, venta {giro.belop}, fekk {f.belop} ({giro.pk})".format(giro=giro, f=f))
                # XXX: Registrer ein donasjon

            giro.innbetalt = f['dato']

            giro.save()

    def stderr(self, msg):
        obj.stderr.write((unicode(msg) + "\n").encode('utf-8'))


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
