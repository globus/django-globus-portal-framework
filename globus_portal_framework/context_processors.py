from django.conf import settings
from django.urls import resolve
from globus_portal_framework import get_index


def globals(request):
    auth_enabled = bool('social_django' in settings.INSTALLED_APPS)
    scopes = getattr(settings, 'SOCIAL_AUTH_GLOBUS_SCOPE', [])
    transfer_scope_set = any(['transfer.api.globus.org' in scope
                              for scope in scopes])
    index = resolve(request.path).kwargs.get('index')
    return {'globus_portal_framework': {
            'project_title': getattr(settings, 'PROJECT_TITLE',
                                     'Globus Portal Framework'),
            'auth_enabled': auth_enabled,
            'transfer_enabled': auth_enabled and transfer_scope_set,
            'index': index,
        }
    }
