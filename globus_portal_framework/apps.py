from django.apps import AppConfig
from django.conf import settings
from globus_portal_framework import settings as dgpf_defaults


class GlobusPortalFrameworkConfig(AppConfig):
    name = 'globus_portal_framework'
    verbose_name = 'Globus Portal Framework'

    def ready(self):
        # Add System checks
        from globus_portal_framework import checks  # noqa


def get_setting(app_setting):
    return getattr(settings, app_setting, getattr(dgpf_defaults, app_setting))
