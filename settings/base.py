# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'medlemssys.urls'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.admin',

    'medlemssys.medlem',
    'reversion',
#   'emencia.django.newsletter',
#   'tagging',
#   'south',
)

#TEMPLATE_CONTEXT_PROCESSORS = (
#   'django.core.context_processors.media',
#   'django.core.context_processors.auth',
#   'django.core.context_processors.request',
#   'django.core.context_processors.i18n',
#   'emencia.django.newsletter.context_processors.media',
#)
