# -*- coding: utf-8 -*-
# vim: ts=4 sts=4 expandtab ai
from os.path import join, dirname

PROJECT_ROOT = dirname(__file__) + "/../"

MEDLEM_CSV = PROJECT_ROOT + "nmu-medl.csv"
GIRO_CSV   = PROJECT_ROOT + "nmu-bet.csv"
LAG_CSV    = PROJECT_ROOT + "nmu-lag.csv"

ALLOWED_HOSTS = ('.nynorsk.no',)

KONTONUMMER = "3450 65 48618"
#MEDIA_ROOT = join(PROJECT_ROOT, 'static')
#MEDIA_URL = '/static/'

TEMPLATE_DIRS = (
    join(PROJECT_ROOT, 'templates'),
)

DEBUG = True
TEMPLATE_DEBUG = DEBUG

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = "Norsk Målungdom <skriv@nynorsk.no>"
SERVER_EMAIL = DEFAULT_FROM_EMAIL

BEHAVIOUR_MODULE = 'behaviour.barnogungdom'

ADMINS = (
    ('Odin', 'odin.omdal@gmail.com'),
)

MANAGERS = ADMINS

AUTH_PROFILE_MODULE = 'medlem.Medlem'

DATABASES = {
    'default': {
       'ENGINE': 'django.db.backends.sqlite3',
       'NAME': join(PROJECT_ROOT, 'db/db.sqlite'),
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
SECRET_KEY = 'e!(o%l1myqy-v(ocxf*xkr)q#=l-^%yxgcod_uicne1wh5ggi1'

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
