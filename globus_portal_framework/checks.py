from django.core.checks import Error, register
from django.conf import settings
import logging

log = logging.getLogger(__name__)
log.debug('Debugging is active.')


@register()
def search_mapper_check(app_configs, **kwargs):
    errors = []
    for index_name, idata in settings.SEARCH_INDEXES.items():
        fields = idata.get('fields')
        if not fields:
            errors.append(Error(
                'Could not find "fields" for settings.{}'.format(index_name)),
                obj=settings,
                id='globus_portal_framework.E001'
            )
    return errors
