#!/usr/bin/env python
# vim: fileencoding=utf-8 shiftwidth=4 tabstop=4 expandtab softtabstop=4 ai
from __future__ import print_function
import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from optparse import make_option

from medlem.models import LokallagOvervaking, Lokallag

class Command(BaseCommand):
    args = '[ delete ]'
    help = 'Opprett (og reinsk inaktive) standard LokallagsOvervakingar'
    option_list = BaseCommand.option_list + (
        make_option('-d', '--delete',
            action='store_true',
            dest='delete',
            default=False,
            help=u"""Slettar alle lokallagsovervakingar som ikkje er spesielle på nokon helst måte (altso: truleg automatisk oppretta)."""),
        )

    def handle(self, *args, **options):
        if options['delete']:
            self.delete_lokallagovervakingar()
        else:
            self.clean_stale()
            self.create_lokallagovervakingar()

    @transaction.commit_on_success
    def clean_stale(self):
        stale = LokallagOvervaking.objects.filter(
            lokallag__aktivt=False,
            epost='',
            medlem__isnull=True,
            deaktivert__isnull=True)
        for lo in stale:
            self.out('Deactivating ' + unicode(lo))
            lo.deaktivert = datetime.datetime.now()
            lo.save()

    @transaction.commit_on_success
    def create_lokallagovervakingar(self):
        new = Lokallag.objects.filter(aktivt=True, lokallagovervaking__isnull=True)
        for n in new:
            lo = LokallagOvervaking(lokallag=n)
            lo.save()
            self.out(u"{}: {}".format(
                    unicode(lo), unicode(lo.epostar())))

    def delete_lokallagovervakingar(self):
        """Slettar alle lokallagsovervakingar som ikkje er spesielle på nokon
        helst måte (altso: truleg automatisk oppretta)."""
        num = LokallagOvervaking.objects.filter(
            epost='',
            medlem__isnull=True).delete()
        self.out("Sletta {} overvakingar.".format(num))

    def err(self, msg):
        self.stderr.write((unicode(msg) + "\n").encode('utf-8'))
    def out(self, msg):
        self.stdout.write((unicode(msg) + "\n").encode('utf-8'))
