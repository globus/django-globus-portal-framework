from django.conf import settings
from django.urls import resolve, reverse, NoReverseMatch, Resolver404
from globus_portal_framework import get_index, IndexNotFound


def globals(request):
    auth_enabled = bool('social_django' in settings.INSTALLED_APPS)
    scopes = getattr(settings, 'SOCIAL_AUTH_GLOBUS_SCOPE', [])
    transfer_scope_set = any(['transfer.api.globus.org' in scope
                              for scope in scopes])

    # Attempt to gather index information on the URL the user is visiting
    # Suppress errors, in case the index isn't valid or registered
    index, index_data = None, {}
    try:
        index = resolve(request.path).kwargs.get('index')
        index_data = get_index(index)
    except (IndexNotFound, Resolver404):
        pass

    # Report if search debugging is enabled so it can be linked in templates
    try:
        reverse('search-debug', args=[index])
        search_debugging_enabled = True
    except NoReverseMatch:
        search_debugging_enabled = False

    return {'globus_portal_framework': {
                'project_title': getattr(settings, 'PROJECT_TITLE',
                                         'Globus Portal Framework'),
                'auth_enabled': auth_enabled,
                'transfer_enabled': auth_enabled and transfer_scope_set,
                'index_data': index_data,
                'index': index,
                'search_debugging_enabled': search_debugging_enabled,
                }
            }
