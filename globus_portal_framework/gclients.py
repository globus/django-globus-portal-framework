from datetime import timedelta
from django.utils import timezone
import globus_sdk
from globus_portal_framework.apps import get_setting
from globus_portal_framework import ExpiredGlobusToken


def validate_token(tok):
    """Validate if the given token is active.

    Returns true if active, raises ExpiredGlobusToken exception if not"""
    ac = globus_sdk.ConfidentialAppAuthClient(
        get_setting('SOCIAL_AUTH_GLOBUS_KEY'),
        get_setting('SOCIAL_AUTH_GLOBUS_SECRET')
    )
    return ac.oauth2_validate_token(tok).get('active', False)


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
