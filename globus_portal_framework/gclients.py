import typing as t
from datetime import timedelta
import django
from django.utils import timezone
from django.conf import settings
from django.utils.module_loading import import_string
import globus_sdk

from globus_portal_framework import ExpiredGlobusToken, exc
from globus_portal_framework.apps import get_setting
from globus_sdk.scopes import Scope, SpecificFlowScopes

import social_django

import logging

log = logging.getLogger(__name__)


def revoke_globus_tokens(user: "django.contrib.auth.models.User"):
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


def is_globus_user(user):
    """
    Check if a Django User has a Globus Association in Python Social Auth.

    :returns: True if Globus association is present. False otherwise.
    """
    if user.is_anonymous:
        return False

    try:
        user.social_auth.get(provider="globus").extra_data
        return True
    except social_django.models.UserSocialAuth.DoesNotExist:
        return False


def load_globus_access_token(user: "django.contrib.auth.models.User", token_name: str = None, resource_server: str = None, scope: str = None):
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
    if token_name:
        log.warning("Passing 'token_name' in 'load_globus_access_token' is deprecated. Use 'resoure_server' instead.")
        resource_server = token_name

    if not user or not user.is_authenticated:
        return None
    if is_globus_user(user) is False:
        if get_setting("GLOBUS_NON_USERS_ALLOWED_PUBLIC_ACCESS") is True:
            log.info(
                f"User {user} is utilizing Globus Services as a non-globus user."
            )
            return None
        else:
            raise exc.NonGlobusUserException(
                f"User {user} does not have"
                " a Globus association in social_django.models.UserSocialAuth"
            )
    tok_list = user.social_auth.get(provider="globus").extra_data
    if token_name == "auth.globus.org":
        return tok_list["access_token"]
    
    service_token_data = None
    for token_data in tok_list.get("other_tokens", []):
        if resource_server and resource_server == token_data["resource_server"]:
            service_token_data = token_data
        elif scope and str(scope) in token_data["scope"]:
            service_token_data = token_data

        if service_token_data:
            exp_td = timedelta(seconds=service_token_data["expires_in"])
            if user.last_login + exp_td < timezone.now():
                raise ExpiredGlobusToken(token_name=token_name)
            return service_token_data["access_token"]

    if token_name:
        raise ValueError(
            f"Attempted to load {token_name} for user {user}, but no "
            f"tokens existed with the name {token_name}, only "
            f"{list(service_tokens.keys())}"
        )
    else:
        raise exc.ScopesRequired(scopes=[scope])

def load_scopes(user: "django.contrib.auth.models.User"):
    extra_data = user.social_auth.get(provider="globus").extra_data
    scopes = []
    for token_data in extra_data.get("other_tokens", []):
        scopes.extend(Scope.parse(s) for s in token_data["scope"].split())
    return scopes

def load_resource_servers(user: "django.contrib.auth.models.User"):
    extra_data = user.social_auth.get(provider="globus").extra_data
    resource_servers = ["auth.globus.org"]
    resource_servers += [td["resource_server"] for td in extra_data.get("other_tokens")]
    return resource_servers


def check_scope_sufficient(user, client, scope: Scope = None):
    """
    TODO: Not sure whether this method should raise, or return the required scope, or needs to be broken into more functions.
    
    """
    if scope:
        if isinstance(scope, str):
            scope = Scope(scope)
        elif not isinstance(scope, Scope):
            raise TypeError("{scope} must be a globus_sdk.scope.Scope object")
        scopes = [s.scope_string for s in load_scopes(user)]
        if scope.scope_string not in scopes:
            raise exc.ScopesRequired(scopes=[str(scope)])
        return
    
    try:
        resource_server = client.resource_server
        if resource_server in load_resource_servers(user):
            return
        raise exc.ScopesRequired(scopes=[client.scopes.all])
    except AttributeError:
        raise ValueError(f"Cannot automatically determine resource server for {client}, scope must be explicitly passed.")
    

def load_globus_client(user: "django.contrib.auth.models.User", client: globus_sdk.BaseClient, token_name: str = None, scope: Scope = None, require_authorized: bool = False) -> globus_sdk.BaseClient:
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
    if token_name:
        log.warning("Passing 'token_name' is deprecated, resource server now automatically determined. Use 'scope' instead or for advanced usage see 'load_globus_access_token'")

    # TODO: This is terrible. Fix it.
    check_scope_sufficient(user, client, scope=scope)
    if scope:
        token = load_globus_access_token(user, scope=scope)
    else:
        token = load_globus_access_token(user, resource_server=client.resource_server)

    if token:
        return client(authorizer=globus_sdk.AccessTokenAuthorizer(token))
    elif not require_authorized:
        return client()
    else:
        raise exc.ScopesRequired(scopes=[client.scopes.all])

def get_default_client_loader():
    return import_string(get_setting('GLOBUS_CLIENT_LOADER'))


def load_auth_client(user: "django.contrib.auth.models.User") -> globus_sdk.AuthClient:
    """
    Load a Globus Auth Client for a logged in user.
    :returns: A live globus_sdk.AuthClient
    """
    load_client = get_default_client_loader()
    return load_client(user, globus_sdk.AuthClient, 'auth.globus.org',
                       require_authorized=True)


def load_search_client(user: "django.contrib.auth.models.User" = None) -> globus_sdk.SearchClient:
    """Load an authorized globus_sdk.SearchClient, for a given logged-in user.
    If user is None, a generic unauthorized search client is loaded instead.
    Unauthorized search clients can still make requests, but may only view
    public records for a search index."""
    load_client = get_default_client_loader()
    return load_client(user, globus_sdk.SearchClient, 'search.api.globus.org')


def load_transfer_client(user: "django.contrib.auth.models.User") -> globus_sdk.TransferClient:
    """
    Load a Globus Transfer Client for a logged in user. Note: A Transfer scope
    must be set in the settings.py file, and a user must be logged in with the
    newest scopes.
    :returns: A live authorized globus_sdk.TransferClient
    """
    load_client = get_default_client_loader()
    return load_client(user, globus_sdk.TransferClient,
                       'transfer.api.globus.org', require_authorized=True)


def load_flows_client(user: "django.contrib.auth.models.User") -> globus_sdk.FlowsClient:
    """
    Load a Globus Flows Client for a logged in user.
    :returns: A live authorized globus_sdk.FlowsClient
    """
    load_client = get_default_client_loader()
    return load_client(user, globus_sdk.FlowsClient,
                       'flows.globus.org', require_authorized=True)


def load_specific_flow_client(user: "django.contrib.auth.models.User", flow_id: str) -> globus_sdk.SpecificFlowClient:
    """
    Load a Specific Flow Client for a given user and flow id. The flow_id must refer
    to a valid and deployed flow, or this will result in an error.

    :returns: A live authorized globus_sdk.SpecificFlowClient
    """
    load_client = get_default_client_loader()
    scope = SpecificFlowScopes(flow_id).user
    token = load_globus_access_token(user, resource_server=flow_id, scope=scope)
    authorizer = globus_sdk.AccessTokenAuthorizer(token)
    fc = globus_sdk.SpecificFlowClient(flow_id, authorizer=authorizer)
    return fc

def get_user_groups(user: "django.contrib.auth.models.User") -> t.Mapping[str, dict]:
    """Get all user groups from the groups.api.globus.org service."""
    groups_client = load_globus_client(user,
                                       globus_sdk.GroupsClient,
                                       'groups.api.globus.org',
                                       require_authorized=True
                                       )
    return groups_client.get_my_groups().data
