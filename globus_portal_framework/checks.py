import logging
from django.core.checks import Error, Warning, register
from django.conf import settings
import globus_sdk

from globus_portal_framework.constants import FILTER_TYPES
from globus_portal_framework.gclients import get_globus_environment

log = logging.getLogger(__name__)
log.debug('Debugging is active.')


@register()
def check_old_v2_config(app_configs, **kwargs):
    warnings = []
    title_template = 'Version 0.3.x Update: "{}" is no longer used'
    OLD_SETTINGS = {
        'ENTRY_SERVICE_VARS':
            {'hint': 'These are now defined in SEARCH_INDEXES under "fields"'},
        'SEARCH_INDEX':
            {'hint': 'This is now defined in SEARCH_INDEXES as "uuid"'},
        'SEARCH_SCHEMA':
            {'hint': 'The JSON in the search schema file have been moved to '
                     'SEARCH_INDEXES, see "fields" and "facets"'},
        'SEARCH_MAPPER':
            {'hint': 'Please replace this with a function in SEARCH_INDEXES '
                     '"fields" for your index. See the README for examples'},
        'SEARCH_ENTRY_FIELD_PATH':
            {'hint': 'The framework no longer assumes all data resides under '
                     'this field, and it has now been removed.'}
    }
    for name, warn_opts in OLD_SETTINGS.items():
        if getattr(settings, name, None):
            warnings.append(Warning(title_template.format(name),
                            hint=warn_opts.get('hint'),
                            obj=settings)
                            )
    return warnings


@register()
def check_old_apps(app_configs, **kwargs):
    installed_apps = getattr(settings, 'INSTALLED_APPS', [])
    old_apps = ['globus_portal_framework.search',
                'globus_portal_framework.transfer']
    if not installed_apps:
        return []
    warn = '{} is now built in, and no longer needs to be explicitly added'
    hint = 'Remove {} from settings.INSTALLED_APPS'
    return [Warning(warn.format(oa),
                    hint=hint.format(oa),
                    obj=settings)
            for oa in old_apps if oa in installed_apps]


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
            errors.append(Error(
                'Could not find "uuid" for settings.SEARCH_INDEXES.{}'
                ''.format(index_name),
                obj=settings,
                hint=('Search UUID for "{}" is "{}".'.format(index_name, id)
                      if id else None),
                id='globus_portal_framework.settings.E001'
                )
            )
        if idata.get('result_format_version') == '2019-08-27':
            errors.append(Warning(
                'Globus Portal Framework does not support '
                'result_format_version=="2019-08-27"',
                obj=settings,
                hint=('Suggested you unset '
                      'settings.SEARCH_INDEXES.{}.result_format_version'
                      ''.format(index_name)),
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
