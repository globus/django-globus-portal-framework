from django.core.checks import Error, Warning, register
from importlib import import_module
import logging


from globus_portal_framework.search import settings

log = logging.getLogger(__name__)
log.debug('Debugging is active.')


@register()
def search_mapper_check(app_configs, **kwargs):
    mod_name, func = settings.SEARCH_MAPPER
    mapper = None
    try:
        mod = import_module(mod_name)
        mapper = getattr(mod, func, None)
    except ModuleNotFoundError:
        pass

    if mapper is None:
        return [Error(
                'Could not find "SEARCH_MAPPER" %s at %s' % (func, mod_name),
                hint='Check "SEARCH_MAPPER" in settings.py is a function '
                     'located at '
                     '"%s"' % '.'.join(settings.SEARCH_MAPPER),
                obj=settings,
                id='globus_portal_framework.search.E001',
                )]

    return []


@register()
def search_schema_check(app_configs, **kwargs):
    try:
        with open(settings.SEARCH_SCHEMA):
            pass
    except FileNotFoundError:
        return [Error(
                'Could not find SEARCH_SCHEMA at %s' % settings.SEARCH_SCHEMA,
                hint='Ensure the path is set correctly in your settings.py',
                obj=settings,
                id='globus_portal_framework.search.E002',
                )]

    return []
