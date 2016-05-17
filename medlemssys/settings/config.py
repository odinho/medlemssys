# -*- coding: utf-8 -*-
# vim: ts=4 sts=4 expandtab ai

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
from os.path import join, dirname

from base import TEMPLATES


PROJECT_ROOT = join(dirname(__file__), '..')
REPO_ROOT = join(PROJECT_ROOT, '..')

MEDLEM_CSV = PROJECT_ROOT + "nmu-medl.csv"
GIRO_CSV   = PROJECT_ROOT + "nmu-bet.csv"
LAG_CSV    = PROJECT_ROOT + "nmu-lag.csv"

ALLOWED_HOSTS = ('.nynorsk.no',)

KONTONUMMER = "3450 65 48618"
ORGNUMMER = "959 358 451"
#MEDIA_ROOT = join(PROJECT_ROOT, 'static')
#MEDIA_URL = '/static/'

TEMPLATES[0]['DIRS'].append(join(PROJECT_ROOT, 'templates'))

DEBUG = True

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = "Norsk Målungdom <skriv@nynorsk.no>"
SERVER_EMAIL = DEFAULT_FROM_EMAIL

BEHAVIOUR_MODULE = 'behaviour.barnogungdom'

ADMINS = (
    ('Odin', 'odin.omdal@gmail.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
       'ENGINE': 'django.db.backends.sqlite3',
       'NAME': join(REPO_ROOT, 'db/db.sqlite'),
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Oslo'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'nn-no'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True
USE_L10N = True

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = join(PROJECT_ROOT, 'static')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)



# Make this unique, and don't share it with anybody.
SECRET_KEY = 'ENDRA_MEG-e!(o%l1myqy-v(ocxf*xkr)q#=l-^%yxgcod_uicne1wh5ggi1'

NEWSLETTER_USE_WORKGROUPS = True
NEWSLETTER_DEFAULT_HEADER_REPLY = NEWSLETTER_DEFAULT_HEADER_SENDER = \
        'Norsk Målungdom <skriv@nynorsk.no>'

# Logging handler, sending email on error
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}
