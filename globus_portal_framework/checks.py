import logging
from django.core.checks import Error, register
from django.conf import settings
import globus_sdk

log = logging.getLogger(__name__)
log.debug('Debugging is active.')


@register()
def check_search_indexes(app_configs, **kwargs):
    errors = []
    for index_name, idata in settings.SEARCH_INDEXES.items():
        if not idata.get('uuid'):
            id = None
            try:
                id = globus_sdk.SearchClient().get_index(index_name).data['id']
            except globus_sdk.exc.SearchAPIError:
                pass
            errors.append(Error(
                'Could not find "uuid" for settings.SEARCH_INDEXES.{}'
                ''.format(index_name),
                obj=settings,
                hint=('Search UUID for "{}" is "{}".'.format(index_name, id)
                      if id else None),
                id='globus_portal_framework.settings.E001'
                )
            )
    return errors
