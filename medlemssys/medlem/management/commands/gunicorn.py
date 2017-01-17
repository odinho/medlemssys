# -*- coding: utf-8 -*-
# vim: shiftwidth=4 tabstop=4 expandtab softtabstop=4 ai

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
#
from __future__ import absolute_import

import argparse
import sys

from django.conf import settings
from django.core.management.base import BaseCommand
from gunicorn.app.wsgiapp import WSGIApplication

from medlemssys.config.wsgi import application


class Command(BaseCommand):
    help = "Run the production web server"

    def add_arguments(self, parser):
        parser.add_argument('args', nargs=argparse.REMAINDER)

    def create_parser(self, *args, **kwargs):
        parser = super(Command, self).create_parser(*args, **kwargs)
        parser.parse_args = lambda args: parser.parse_known_args(args)[0]
        return parser

    def handle(self, *args, **options):
        # some argv trickery to reuse max of gunicorn wsgiapp
        # prefer this to a more programmatic way
        sys.argv = sys.argv[1:]
        app = settings.WSGI_APPLICATION.rsplit('.', 1)
        sys.argv.append(':'.join(app))
        WSGIApplication().run()
