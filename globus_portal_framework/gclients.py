import requests
from datetime import timedelta
from packaging.version import Version
from django.utils import timezone
from django.conf import settings
from django.utils.module_loading import import_string
import globus_sdk

from globus_portal_framework import ExpiredGlobusToken, exc
from globus_portal_framework.apps import get_setting

import logging

log = logging.getLogger(__name__)

GLOBUS_SDK_VERSION = Version(globus_sdk.version.__version__)

if GLOBUS_SDK_VERSION.major >= 3:
    # Skip any versions less than 3.9
    if GLOBUS_SDK_VERSION.major == 3 and GLOBUS_SDK_VERSION.minor < 9:
        pass
    else:
        globus_sdk._force_eager_imports()

# This is legacy code for pre SDK-v3.3.x versions, it will be removed in the
# next version of DGPF.
CUSTOM_ENVS = {
    'auth': {
        'default': 'https://auth.globus.org',
        'production': 'https://auth.globus.org'
    },
    'groups': {
        # Globus SDK v2
        'default': 'https://groups.api.globus.org',
        # Globus SDK v3
        'production': 'https://groups.api.globus.org',
        'preview': 'https://groups.api.preview.globus.org',
    }
}

# This is present in the latest v3 version of the Globus SDK
# and will be removed in the next version. 
GROUPS_SCOPE = ('urn:globus:auth:scope:groups.api.globus.org:'
                'view_my_groups_and_memberships')
GLOBUS_GROUPS_V2_MY_GROUPS = '/v2/groups/my_groups'


def get_globus_environment():
    """
    This is needed to support prior versions of the Globus SDK < 3.3.x, please
    use the following for determining service urls instead:

    https://globus-sdk-python.readthedocs.io/en/stable/config.html#config-related-functions  # noqqa
    """
    try:
        return globus_sdk.config.get_globus_environ()
    except AttributeError:
        return globus_sdk.config.get_environment_name()


def get_service_url(service_name):
    """This is needed for backwards compatibility with earlier versions of the
    Globus SDK. Use the following supported function in the Globus SDK instead:
    https://globus-sdk-python.readthedocs.io/en/stable/config.html#globus_sdk.config.get_service_url  # noqa
    """
    env = get_globus_environment()
    if service_name in CUSTOM_ENVS:
        if env not in CUSTOM_ENVS[service_name]:
            err = ('Service {} has no service url for the '
                   'configured environment: "{}"'.format(service_name, env))
            raise exc.GlobusPortalException('InvalidEnv', err)
        return CUSTOM_ENVS[service_name][env]
    if GLOBUS_SDK_VERSION.major == 3 and GLOBUS_SDK_VERSION.minor in [0, 1, 2]:
        return globus_sdk.config.get_service_url(env, service_name)
    elif GLOBUS_SDK_VERSION.major == 3 and GLOBUS_SDK_VERSION.minor >= 3:
        return globus_sdk.config.get_service_url(service_name)


def validate_token(tok):
    """Validate if the given token is active.

    Returns true if active, raises ExpiredGlobusToken exception if not"""
    ac = globus_sdk.ConfidentialAppAuthClient(
        settings.SOCIAL_AUTH_GLOBUS_KEY,
        settings.SOCIAL_AUTH_GLOBUS_SECRET
    )
    return ac.oauth2_validate_token(tok).get('active', False)


def revoke_globus_tokens(user):
    """
    Revoke all of a user's Globus tokens.
    :param user:
    :return:
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
        raise exc.PortalAuthException(
            message='Authenticated User {} has no tokens for {}. Is {} missing '
                    'from SOCIAL_AUTH_GLOBUS_SCOPE?'.format(user, client,
                                                            token_name))


def get_default_client_loader():
    return import_string(get_setting('GLOBUS_CLIENT_LOADER'))


def load_auth_client(user):
    load_client = get_default_client_loader()
    return load_client(user, globus_sdk.AuthClient, 'auth.globus.org',
                       require_authorized=True)


def load_search_client(user=None):
    """Load a globus_sdk.SearchClient, with a token authorizer if the user is
    logged in or a generic one otherwise."""
    load_client = get_default_client_loader()
    return load_client(user, globus_sdk.SearchClient, 'search.api.globus.org')


def load_transfer_client(user):
    load_client = get_default_client_loader()
    return load_client(user, globus_sdk.TransferClient,
                       'transfer.api.globus.org', require_authorized=True)


def get_user_groups(user):
    """Get all user groups from the groups.api.globus.org service."""
    try:
        GROUPS_RS = '04896e9e-b98e-437e-becd-8084b9e234a0'
        token = load_globus_access_token(user, GROUPS_RS)
        log.debug('Fetched old-style groups token')
    except ValueError:
        log.debug('Fetched new-style groups token. Old style can now be '
                  'removed.')
        token = load_globus_access_token(user, 'groups.api.globus.org')
    # Attempt to load the access token for Globus Groups. The scope name will
    # change Sept 23rd, at which point attempting to fetch via the old name
    # can be removed.
    groups_service = get_service_url('groups')
    groups_url = '{}{}'.format(groups_service, GLOBUS_GROUPS_V2_MY_GROUPS)
    headers = {'Authorization': 'Bearer ' + token}
    response = requests.get(groups_url, headers=headers)
    try:
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as httpe:
        log.error(response.text)
        raise exc.GroupsException(message='Failed to get groups info for user '
                                          '{}: {}'.format(user, httpe))
