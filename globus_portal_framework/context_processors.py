from django.conf import settings


def globals(request):
    auth_enabled = bool('social_django' in settings.INSTALLED_APPS)
    scopes = getattr(settings, 'SOCIAL_AUTH_GLOBUS_SCOPE', [])
    transfer_scope_set = any(['transfer.api.globus.org' in scope
                              for scope in scopes])
    preview_setup = bool(
        getattr(settings, 'GLOBUS_HTTP_ENDPOINT', False) and
        getattr(settings, 'PREVIEW_TOKEN_NAME', False)
    )

    return {
        'project_title': getattr(settings, 'PROJECT_TITLE',
                                 'Globus Portal Framework'),
        'auth_enabled': auth_enabled,
        'transfer_enabled': auth_enabled and transfer_scope_set,
        'preview_enabled': auth_enabled and preview_setup
    }
