# -*- coding: utf-8 -*-
"""
Production Configurations

You need to go through this file and change the settings.

"""
from __future__ import absolute_import, unicode_literals

import os

from medlemssys.config.settings import *  # noqa


DEBUG = True
if DEBUG:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(os.path.normpath(os.path.dirname(__file__)),
                                 'db.sqlite'),
        }
    }

# Hosts/domain names that are valid for this site
ALLOWED_HOSTS = []

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'ENDRA_MEG-e!(o%l1myqy-v(ocxf*xkr)q#=l-^%yxgcod_uicne1wh5ggi1'

# Token used for creating medlems via API. To stop stupid bots.
INNMELDING_TOKEN = ''

# Used for allowing CORS, and where the ?next= redirector can point
TRUSTED_EXTERNAL_DOMAINS = []

# This can be used to implement specific behaviours [barnogungdom, base]
BEHAVIOUR_MODULE = 'medlemssys.behaviour.barnogungdom'

# Installation specific data
KONTONUMMER = '3450 65 48618'
ORGNUMMER = '959 358 451'

# Email
DEFAULT_FROM_EMAIL = 'Medlemssys <noreply@medlemssys.s0.no>'
EMAIL_SUBJECT_PREFIX = '[Medlemssys] '
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Database configuration
# See: https://docs.djangoproject.com/en/dev/ref/settings/#databases
#DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.postgresql',
#        'NAME': 'medlemssys',
#        'USER': '',
#        'PASSWORD': '',
#    }
#}

#
# Less frequently changed settings
#

# Custom Admin URL
#ADMIN_URL = r'^admin/'

# Use Whitenoise to serve static files
# See: https://whitenoise.readthedocs.io/
#STATIC_ROOT = ''
MIDDLEWARE_CLASSES = (
    'whitenoise.middleware.WhiteNoiseMiddleware',) + MIDDLEWARE_CLASSES
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# SECURITY CONFIGURATION
# See https://docs.djangoproject.com/en/1.9/ref/middleware/#module-django.middleware.security
# and https://docs.djangoproject.com/ja/1.9/howto/deployment/checklist/#run-manage-py-check-deploy

# set this to 60 seconds and then to 518400 when you can prove it works
#SECURE_HSTS_SECONDS = 60
#SECURE_HSTS_INCLUDE_SUBDOMAINS = True
#SECURE_CONTENT_TYPE_NOSNIFF = True
#SECURE_BROWSER_XSS_FILTER = True
#SESSION_COOKIE_SECURE = True
#SESSION_COOKIE_HTTPONLY = True
#SECURE_SSL_REDIRECT = True
#CSRF_COOKIE_SECURE = True
#CSRF_COOKIE_HTTPONLY = True
#X_FRAME_OPTIONS = 'DENY'

if not DEBUG:
    INSTALLED_APPS += ('gunicorn', )


# Template configuration
# See:
# https://docs.djangoproject.com/en/dev/ref/templates/api/#django.template.loaders.cached.Loader
TEMPLATES[0]['OPTIONS']['loaders'] = [
    ('django.template.loaders.cached.Loader', [
         'django.template.loaders.filesystem.Loader',
         'django.template.loaders.app_directories.Loader',
     ]),
]

# Caching
# Comment out to enable, you obviously need Redis running.
"""
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/0',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'IGNORE_EXCEPTIONS': True,  # mimics memcache behavior.
                                        # http://niwinz.github.io/django-redis/latest/#_memcached_exceptions_behavior
        }
    }
}
"""


# Raven Sentry client
# This is currently disabled. You need to install `raven` and comment out this
# configuration.
# See https://docs.getsentry.com/hosted/clients/python/integrations/django/
"""
INSTALLED_APPS += ('raven.contrib.django.raven_compat', )
MIDDLEWARE_CLASSES = (
    'raven.contrib.django.raven_compat.middleware.'
    'SentryResponseErrorIdMiddleware',) + MIDDLEWARE_CLASSES

# Sentry Configuration
SENTRY_DSN = 'your-dsn'
SENTRY_CLIENT = 'raven.contrib.django.raven_compat.DjangoClient'
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'root': {
        'level': 'WARNING',
        'handlers': ['sentry'],
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s '
                      '%(process)d %(thread)d %(message)s'
        },
    },
    'handlers': {
        'sentry': {
            'level': 'ERROR',
            'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'django.db.backends': {
            'level': 'ERROR',
            'handlers': ['console'],
            'propagate': False,
        },
        'raven': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'sentry.errors': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'django.security.DisallowedHost': {
            'level': 'ERROR',
            'handlers': ['console', 'sentry'],
            'propagate': False,
        },
    },
}
RAVEN_CONFIG = {
    'DSN': SENTRY_DSN
}
"""
# Raven end
