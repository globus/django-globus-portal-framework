"""
is_active is a template tag to check whether this is the currently
active page, and will output ``active`` if the page is active, or
the empty string ``""`` if the page is not active. It is useful working
within bootstrap templates which use the ``active`` tag. An example is
nav items:

.. code-block::

    {# templates/globus-portal-framework/v3/components/search-nav.html #}
    {% load static is_active %}

    <div class="subnav mt-auto bottom-border-0">
    <ul class="nav nav-tabs nav-search-nav justify-content-center">
        <li class="mt-auto">
        <a class="btn btn-primary btn-lg border-0 squared {% is_active request 'search' index=globus_portal_framework.index %}" role="button"
            href="{% url 'search' globus_portal_framework.index %}">Search</a>
        </li>
        <li class="mt-auto">
        <a class="btn btn-primary btn-lg border-0 squared {% is_active request 'search-about' index=globus_portal_framework.index %}" role="button"
            href="{% url 'search-about' globus_portal_framework.index %}">About</a>
        </li>
    </ul>
    </div>

In the example above, "Search" will become active when the user navigates to the search view, but will leave "About" inactive.

"""
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
