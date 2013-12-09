#!/usr/bin/env python
# vim: fileencoding=utf-8 shiftwidth=4 tabstop=4 expandtab softtabstop=4 ai
from __future__ import print_function
from django.core.management.base import BaseCommand


from ...actions import add_missing_giros

class Command(BaseCommand):
    def handle(self, *args, **options):
        was_missing = add_missing_giros()
        if was_missing:
            print('Created {} previously missing giros'.format(len(was_missing)))
