import logging
import os
from django.core.checks import Error, Warning, Info, register
from django.conf import settings
import globus_sdk

from globus_portal_framework.constants import FILTER_TYPES
from globus_portal_framework.gclients import get_globus_environment

log = logging.getLogger(__name__)
log.debug('Debugging is active.')


@register()
def check_search_indexes(app_configs, **kwargs):
    errors = []
    search_indexes = getattr(settings, 'SEARCH_INDEXES', {})
    for index_name, idata in search_indexes.items():
        if not idata.get('uuid'):
            id = None
            try:
                sc = globus_sdk.SearchClient()
                r = sc.get_index(index_name)
                id = r.data['id']
            except globus_sdk.SearchAPIError:
                pass
            hint = f'Search UUID for "{index_name}" is "{id}".' if id else None
            errors.append(Error(
                'Could not find "uuid" for '
                f'settings.SEARCH_INDEXES.{index_name}',
                obj=settings,
                hint=hint,
                id='globus_portal_framework.settings.E001'
                )
            )
        rf_version = idata.get('result_format_version')
        if rf_version and rf_version != DEFAULT_RESULT_FORMAT_VERSION:
            errors.append(Warning(
                'Globus Portal Framework does not support '
                f'result_format_version=="{rf_version}"',
                obj=settings,
                hint=('Suggested you unset settings.SEARCH_INDEXES.'
                      f'{index_name}.result_format_version'),
                id='globus_portal_framework.settings.E002'
                )
            )
        fm = idata.get('filter_match', None)
        if fm is not None and fm not in FILTER_TYPES.keys():
            errors.append(
                Warning('SEARCH_INDEXES.{}.filter_match is invalid.'
                        ''.format(index_name),
                        obj=settings,
                        hint='Must be one of {}'.format(
                            tuple(FILTER_TYPES.keys()))
                        ))
    return errors


@register()
def check_globus_env(app_configs, **kwargs):
    env = get_globus_environment()
    # 'default' is used in Globus SDK v2, 'production' in v3
    if env not in ['default', 'production']:
        return [Warning('Environment set to "{}", unset with '
                        '"unset GLOBUS_SDK_ENVIRONMENT"'.format(env))]
    return []
