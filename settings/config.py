from os.path import join, dirname

PROJECT_ROOT = dirname(__file__) + "/../"

MEDIA_ROOT = join(PROJECT_ROOT, 'static')
MEDIA_URL = '/static/'

TEMPLATE_DIRS = (
    join(PROJECT_ROOT, 'templates'),
)

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Odin', 'odin.omdal@gmail.com'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = join(PROJECT_ROOT, 'db/db.sqlite')
DATABASE_USER = ''             # Not used with sqlite3.
DATABASE_PASSWORD = ''         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

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

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = MEDIA_URL + 'admin/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'e!(o%l1myqy-v(ocxf*xkr)q#=l-^%yxgcod_uicne1wh5ggi1'

