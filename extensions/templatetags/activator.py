from django import template
from django.core.urlresolvers import reverse

register = template.Library()

@register.simple_tag
def activator(request, url):
    if request:
        if url:
            if url in request.path:
                return 'active'
    else:
        if not url:
            return 'active'

    return ""