from datetime import timedelta
from django.utils import timezone
from django.conf import settings
import globus_sdk

from globus_portal_framework import ExpiredGlobusToken


def validate_token(tok):
    """Validate if the given token is active.

    Returns true if active, raises ExpiredGlobusToken exception if not"""
    auth_client = load_globus_confidential_client()
    return auth_client.oauth2_validate_token(tok).get('active', False)


def load_globus_access_token(user, token_name):
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
                raise ValueError('Attempted to load {} for user {}, but no '
                                 'tokens existed with the name {}, only {}'
                                 ''.format(token_name, user, token_name,
                                           list(service_tokens.keys())))


def load_globus_confidential_client(client_id=None):
    """Load a confidential client. With no parameters, this returns a client
    based on the built-in Globus Client/Secret used for the portal. If more
    clients are configured in settings.CONFIDENTIAL_CLIENTS, passing in a
    client_id for one of those will yield a Globus client for that id/secret.
    Returns: globus_sdk.ConfidentialAppAuthClient
    Raises: ValueError, if the client_id is not in CONFIDENTIAL_CLIENTS
    """
    if client_id is None or client_id == settings.SOCIAL_AUTH_GLOBUS_KEY:
        return globus_sdk.ConfidentialAppAuthClient(
            client_id=settings.SOCIAL_AUTH_GLOBUS_KEY,
            client_secret=settings.SOCIAL_AUTH_GLOBUS_SECRET
        )
    try:
        clients = {c['client_id']: c
                   for c in getattr(settings, 'CONFIDENTIAL_CLIENTS')}
        return globus_sdk.ConfidentialAppAuthClient(
            client_id=clients[client_id]['client_id'],
            client_secret=clients[client_id]['client_secret']
        )
    except (KeyError, AttributeError):
        raise ValueError('The Globus App Client ID "{}" has not been '
                         'configured in settings.CONFIDENTIAL_CLIENTS'
                         ''.format(client_id)) from None


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
        raise ValueError(
            'User {} has not been authorized for {}'.format(user, client))


def load_auth_client(user):
    return load_globus_client(user, globus_sdk.AuthClient,
                              'auth.globus.org', require_authorized=True)


def load_search_client(user=None):
    """Load a globus_sdk.SearchClient, with a token authorizer if the user is
    logged in or a generic one otherwise."""
    return load_globus_client(user, globus_sdk.SearchClient,
                              'search.api.globus.org')


def load_transfer_client(user):
    return load_globus_client(user, globus_sdk.TransferClient,
                              'transfer.api.globus.org')
