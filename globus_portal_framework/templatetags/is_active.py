import logging
from django.template import Library
from django.urls import resolve
from django.urls.exceptions import Resolver404
register = Library()

log = logging.getLogger(__name__)


@register.simple_tag
def is_active(request, url_name, **url_kwargs):
    view = ''
    try:
        res = resolve(request.path)
        if res.kwargs == url_kwargs and url_name == res.url_name:
            view = 'active'
    except Resolver404 as nfe:
        log.exception(nfe)
        log.error('Are you passing the correct args for {}?'.format(url_name))
    log.debug(f'{url_name}: Is Active? {True if view else False}')
    return view
