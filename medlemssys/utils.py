from urlparse import urlparse

from django.conf import settings
from django.shortcuts import redirect


def add_cors(func):
    def decorator(request, *args, **kwargs):
        response = func(request, *args, **kwargs)
        origin = request.META.get('HTTP_ORIGIN')
        if (origin and
            _host(origin) in settings.TRUSTED_EXTERNAL_DOMAINS):
            response['Access-Control-Allow-Origin'] = origin
        return response
    return decorator

def _host(url):
   return urlparse(url).hostname
