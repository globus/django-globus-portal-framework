from django.core.checks import Warning, register


@register()
def app_no_longer_needed(app_configs, **kwargs):
    return [Warning('"globus_portal_framework.search" is no longer required.',
            hint=('Remove "globus_portal_framework.search" from '
                  'INSTALLED_APPS in your settings.py'),
            id='globus_portal_framework.search.E001',
            )]
