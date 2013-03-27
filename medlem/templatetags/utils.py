from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
@stringfilter
def split(str,splitter=","):
    return str.split(splitter)

@register.simple_tag
def val_option(medlem, val, not_val):
    selected = ''
    if (all(medlem.val_exists(v) for v in val.split(',')) and
            not any(medlem.val_exists(v) for v in not_val.split(','))):
        selected='selected'
    return u'<option {sel} value="{value}">'.format(sel=selected, value=val)

@register.simple_tag
def val_checked(medlem, val):
    if medlem.val_exists(val):
        return 'checked'
    return ''
