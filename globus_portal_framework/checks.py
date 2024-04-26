import logging
import os
import uuid
from django.core.checks import Error, Warning, Info, register
from django.conf import settings
import globus_sdk

from globus_portal_framework.constants import (
    FILTER_TYPES
)

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
        fm = idata.get('filter_match', None)
        if fm is not None and fm not in FILTER_TYPES.keys():
            errors.append(
                Warning('SEARCH_INDEXES.{}.filter_match is invalid.'
                        ''.format(index_name),
                        obj=settings,
                        hint=f'Must be one of {tuple(FILTER_TYPES.keys())}'
                        ))
    return errors


@register()
def check_globus_env(app_configs, **kwargs):
    env = os.getenv('GLOBUS_SDK_ENVIRONMENT')
    if env and env != 'production':
        return [Info(f'GLOBUS_SDK_ENVIRONMENT set to "{env}".',
                     hint='Non-production services may contain experimental '
                          'features.')]
    return []


@register()
def check_allowed_groups(app_configs, **kwargs):
    if not getattr(settings, 'SOCIAL_AUTH_GLOBUS_ALLOWED_GROUPS', None):
        return []

    if not isinstance(settings.SOCIAL_AUTH_GLOBUS_ALLOWED_GROUPS, list):
        return [Error('SOCIAL_AUTH_GLOBUS_ALLOWED_GROUPS must be a list',
                obj=settings, id='globus_portal_framework.settings.E002')]

    errors = []
    for idx, group in enumerate(settings.SOCIAL_AUTH_GLOBUS_ALLOWED_GROUPS):
        for attr in ('name', 'uuid'):
            if attr not in group:
                e = Error(f'Entry {idx} in SOCIAL_AUTH_GLOBUS_ALLOWED_GROUPS missing required attribute "{attr}"',
                          obj=settings, id='globus_portal_framework.settings.E003')
                errors.append(e)

        if 'uuid' in group:
            try:
                uuid.UUID(group['uuid'])
            except ValueError:
                e = Error(f'Entry {idx} in SOCIAL_AUTH_GLOBUS_ALLOWED_GROUPS: {group["uuid"]} is not a UUID!',
                          obj=settings, id='globus_portal_framework.settings.E004')
                errors.append(e)

    return errors
