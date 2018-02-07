from django.core.checks import Error, Warning, register
from django.conf import settings
from importlib import import_module
import logging

log = logging.getLogger(__name__)
log.debug('Debugging is active.')


@register()
def search_schema_check(app_configs, **kwargs):
    if not hasattr(settings, 'SEARCH_MAPPER'):
        return [Error(
                'SEARCH_MAPPER is not defined.',
                hint='Set SEARCH_MAPPER in your settings.py',
                obj=settings,
                id='api.E001',
                )]

    mod_name, func = settings.SEARCH_MAPPER
    mod = import_module(mod_name)
    mapper = getattr(mod, func, None)
    if not mapper:
        return [Error(
                'Could not find custom mapper %s at %s' % (func, mod_name),
                hint='Ensure the path is set correctly',
                obj=settings,
                id='api.E002',
                )]

    return []
