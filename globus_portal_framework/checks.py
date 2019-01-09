import logging
from django.core.checks import Error, Warning, register
from django.conf import settings
import globus_sdk

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
