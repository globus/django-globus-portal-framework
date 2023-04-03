from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.utils.module_loading import import_string
import globus_sdk

from globus_portal_framework import ExpiredGlobusToken, exc
from globus_portal_framework.apps import get_setting

import logging

log = logging.getLogger(__name__)


def validate_token(tok):
    """Validate if the given token is active.

    :returns: True if active
    :raises globus_sdk.ExpiredGlobusToken: if token has expired."""
    ac = globus_sdk.ConfidentialAppAuthClient(
        settings.SOCIAL_AUTH_GLOBUS_KEY,
        settings.SOCIAL_AUTH_GLOBUS_SECRET
    )
    return ac.oauth2_validate_token(tok).get('active', False)


def revoke_globus_tokens(user):
    """
    Revoke all of a user's Globus tokens.
    :param user: A django user object, typically on the request of a view
        (request.user)
    :return: None
    """
    tokens = user.social_auth.get(provider='globus').extra_data
    ac = globus_sdk.ConfidentialAppAuthClient(
        settings.SOCIAL_AUTH_GLOBUS_KEY,
        settings.SOCIAL_AUTH_GLOBUS_SECRET
    )
    tok_list = [(tokens['access_token'], tokens.get('refresh_token'))]
    tok_list.extend([(t['access_token'], t.get('refresh_token'))
                    for t in tokens.get('other_tokens', [])])

    for at, rt in tok_list:
        try:
            ac.oauth2_revoke_token(at)
            if rt:
                ac.oauth2_revoke_token(rt)
        except globus_sdk.GlobusAPIError as gapie:
            log.exception(gapie)

    # Gather info on what was revoked
    access, refresh = zip(*tok_list)
    at, rt = filter(None, access), filter(None, refresh)
    num_at, num_rt = len(list(at)), len(list(rt))
    log.info(f'Revoked {num_at + num_rt} ({num_at} access, {num_rt} refresh) '
             f'tokens for user {user}')


def load_globus_access_token(user, token_name):
    """
    Load a globus user access token using a provided lookup by resource server.
    Scopes MUST have already been configured in settings.py, and additionally
    a user must have already gone through an auth flow and logged into Globus.

    An example of this may look like the following:

    def myview(request):
        token = load_globus_access_token(request.user,
                                         'transfer.api.globus.org')

    :param user: A Django User object. Usually this comes from request.user
    :param token_name: The name of a token by resource server
    :raises ValueError: If no tokens match the token name given
    """
    if not user:
        return None
    if user.is_authenticated:
        tok_list = user.social_auth.get(provider='globus').extra_data
        if token_name == 'auth.globus.org':
            return tok_list['access_token']
        if tok_list.get('other_tokens'):
            service_tokens = {t['resource_server']: t
                              for t in tok_list['other_tokens']}
            service_token = service_tokens.get(token_name)
            if service_token:
                exp_td = timedelta(seconds=service_token['expires_in'])
                if user.last_login + exp_td < timezone.now():
                    raise ExpiredGlobusToken(token_name=token_name)
                return service_token['access_token']
            else:
                raise ValueError(
                    f'Attempted to load {token_name} for user {user}, but no '
                    f'tokens existed with the name {token_name}, only '
                    f'{list(service_tokens.keys())}'
                )


def load_globus_client(user, client, token_name, require_authorized=False):
    """Load a globus client with a given user and the name of the token. If
    the user is Anonymous (Not logged in), then an unauthenticated client is
    returned. If the client is logged in and the token is not found, a
    ValueError is raised.

    Example:
        >>> u = django.contrib.auth.models.User.objects.get(username='bob')
        >>> load_globus_client(u, globus_sdk.SearchClient, 'search.api.globus.org')  # noqa
    Given that bob is a logged in user, they will now have a search
    client capable of making searches on confidential data.
    Example2:
        >>> u = django.contrib.auth.models.AnonymousUser
        >>> load_globus_client(u, globus_sdk.SearchClient, 'search.api.globus.org')  # noqa
    An 'AnonymousUser' is not logged in, so they will get a regular search
    client and can only search on public data.
    """
    token = load_globus_access_token(user, token_name)
    if token:
        return client(authorizer=globus_sdk.AccessTokenAuthorizer(token))
    elif not require_authorized:
        return client()
    else:
        raise exc.PortalAuthException(
            message='Authenticated User {} has no tokens for {}. Is {} missing '
                    'from SOCIAL_AUTH_GLOBUS_SCOPE?'.format(user, client,
                                                            token_name))


def get_default_client_loader():
    return import_string(get_setting('GLOBUS_CLIENT_LOADER'))


def load_auth_client(user):
    """
    Load a Globus Auth Client for a logged in user.
    :returns: A live globus_sdk.AuthClient
    """
    load_client = get_default_client_loader()
    return load_client(user, globus_sdk.AuthClient, 'auth.globus.org',
                       require_authorized=True)


def load_search_client(user=None):
    """Load an authorized globus_sdk.SearchClient, for a given logged-in user.
    If user is None, a generic unauthorized search client is loaded instead.
    Unauthorized search clients can still make requests, but may only view
    public records for a search index."""
    load_client = get_default_client_loader()
    return load_client(user, globus_sdk.SearchClient, 'search.api.globus.org')


def load_transfer_client(user):
    """
    Load a Globus Transfer Client for a logged in user. Note: A Transfer scope
    must be set in the settings.py file, and a user must be logged in with the
    newest scopes.
    :returns: A live authorized globus_sdk.TransferClient
    """
    load_client = get_default_client_loader()
    return load_client(user, globus_sdk.TransferClient,
                       'transfer.api.globus.org', require_authorized=True)


def get_user_groups(user):
    """Get all user groups from the groups.api.globus.org service."""
    groups_client = load_globus_client(user,
                                       globus_sdk.GroupsClient,
                                       'groups.api.globus.org',
                                       require_authorized=True
                                       )
    return groups_client.get_my_groups().data
