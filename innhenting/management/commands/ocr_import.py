#!/usr/bin/env python
# vim: fileencoding=utf-8 shiftwidth=4 tabstop=4 expandtab softtabstop=4 ai
from __future__ import print_function
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
import os

from medlemssys.medlem.models import Giro
from medlemssys.medlem.models import update_denormalized_fields
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
                self.err("Fann ikkje giroen, {dato:6s} {belop:4n} {kid:12s} {transaksjon}".format(**f))
                continue

            if f['belop'] < giro.belop:
                self.err("{giro}: for lite betalt! Rekna {giro.belop}, fekk {belop} ({giro.pk})".format(giro=giro, belop=f['belop']))
            elif f['belop'] > giro.belop:
                # XXX: Splitt opp? Registrer ein donasjon?
                self.err("{giro}: Betalte meir, venta {giro.belop}, fekk {belop} ({giro.pk})".format(giro=giro, belop=f['belop']))
                giro.innbetalt = f['dato']
            else:
                giro.innbetalt = f['dato']
                self.err("{belop:3n}kr ({giro.pk}) {giro} ".format(giro=giro, belop=f['belop']))

            giro.innbetalt_belop = f['belop']
            giro.save()

    def err(self, msg):
        self.stderr.write((unicode(msg) + "\n").encode('utf-8'))
