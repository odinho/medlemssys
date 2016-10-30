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

def add_next_redirect(func):
    def decorator(request, *args, **kwargs):
        next_ = request.GET.get('next')
        response = func(request, *args, **kwargs)
        if (next_ and
            _host(next_) in settings.TRUSTED_EXTERNAL_DOMAINS and
            200 <= response.status_code < 300):
            return redirect(next_)
        return response
    return decorator

def _host(url):
   return urlparse(url).hostname
