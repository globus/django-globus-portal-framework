import pytest
import social_core
from unittest.mock import Mock

from tests.mocks import mock_tokens
from globus_portal_framework.auth import GlobusOpenIdConnect


@pytest.fixture
def groups():
    return [
        {
            'name': 'Test Group 1',
            'enforce_session': False,
            'group_type': 'regular',
            'id': 'test-group-1-uuid',
            'my_memberships': [{
                'group_id': 'test-group-1-uuid',
                'identity_id': 'mal-ident-1-uuid',
                'role': 'manager',
                'username': 'mal@globusid.org'
            }
            ]
        },
        {
            'name': 'Test Group 2',
            'enforce_session': False,
            'group_type': 'regular',
            'id': 'test-group-2-uuid',
            'my_memberships': [
                {
                    'group_id': 'test-group-2-uuid',
                    'identity_id': 'mal-ident-2-uuid',
                    'role': 'member',
                    'username': 'mal@anl.gov'
                }
            ]
        }
    ]


@pytest.fixture
def user_details():
    return {
        'username': 'mal@globusid.org',
        'email': 'mal@globus.org',
        'fullname': 'Malcolm Reynolds',
        'first_name': 'Malcolm',
        'last_name': 'Reynolds',
        'identity_id': 'mal-ident-1-uuid',
        'idp_id': 'ident-uuid',
        'identities': [],
    }


@pytest.fixture
def mock_group_tokens():
    tokens = mock_tokens(['groups.api.globus.org'])
    tokens[0]['scope'] = 'urn:globus:auth:scope:groups.api.globus.org:' \
                         'view_my_groups_and_memberships'
    return tokens


@pytest.fixture
def tokens():
    return mock_tokens(['urn:globus:auth:scope:groups.api.globus.org:'
                       'view_my_groups_and_memberships'])


@pytest.fixture
def get_json(monkeypatch):
    monkeypatch.setattr(GlobusOpenIdConnect, 'get_json', Mock())
    return GlobusOpenIdConnect.get_json


@pytest.fixture
def introspect_response(monkeypatch, settings):
    resp = {
        'active': True,
        'aud': ['auth.globus.org', settings.SOCIAL_AUTH_GLOBUS_KEY],
        'client_id': settings.SOCIAL_AUTH_GLOBUS_KEY,
        'dependent_tokens_cache_id': '8fa8acb8bdafda7a4138c70607a32d4e'
                                     '83179f319be6823ff0c8549908adbf85',
        'email': 'mal@globus.org',
        'exp': 1632671003,
        'iat': 1632498203,
        'identities_set': [
            'mal-ident-1-uuid',
        ],
        'iss': 'https://auth.globus.org',
        'name': 'Malcolm Reynolds',
        'nbf': 1632498203,
        'scope': 'profile openid email',
        'session_info': {
            'authentications': {
                'mal-ident-1-uuid': {
                    'acr': 'urn:oasis:names:tc:SAML:2.0:ac:classes:'
                           'PasswordProtectedTransport',
                    'amr': None,
                    'auth_time': 1632498192,
                    'idp': 'ident-uuid'},
            },
            'session_id': 'f89aded8-bacd-4a6f-819b-ecb1fd353779'
        },
        'sub': 'mal-sub-uuid',
        'token_type': 'Bearer',
        'username': 'mal@globusid.org'
    }
    monkeypatch.setattr(GlobusOpenIdConnect, 'introspect_token',
                        Mock(return_value=resp))
    return GlobusOpenIdConnect.introspect_token


@pytest.fixture
def globus_identities(monkeypatch):
    r = {
        'identities': [{
            'email': 'mal@globus.org',
            'id': 'mal-ident-1-uuid',
            'identity_provider': 'ident-uuid',
            'identity_type': 'login',
            'name': 'Malcolm Reynolds',
            'organization': None,
            'status': 'used',
            'username': 'mal@globus.org'
        }],
        'included': {
            'identity_providers': [{
                'alternative_names': ['Globus'],
                'domains': ['globus.org'],
                'id': 'ident-uuid',
                'name': 'Globus',
                'short_name': 'globus'
            }]
        }
    }
    monkeypatch.setattr(GlobusOpenIdConnect, 'get_globus_identities',
                        Mock(return_value=r))
    return GlobusOpenIdConnect.get_globus_identities


def test_get_user_details(introspect_response, globus_identities):
    goidc = GlobusOpenIdConnect()
    details = goidc.get_user_details({'access_token': 'mock_access_token',
                                      'identities_set': []})
    assert details == {
        'email': 'mal@globus.org',
        'first_name': 'Malcolm',
        'fullname': 'Malcolm Reynolds',
        'identities': {'identities': [{'email': 'mal@globus.org',
                                       'id': 'mal-ident-1-uuid',
                                       'identity_provider': 'ident-uuid',
                                       'identity_type': 'login',
                                       'name': 'Malcolm Reynolds',
                                       'organization': None,
                                       'status': 'used',
                                       'username': 'mal@globus.org'}],
                       'included': {'identity_providers': [
                           {'alternative_names': ['Globus'],
                            'domains': ['globus.org'],
                            'id': 'ident-uuid',
                            'name': 'Globus',
                            'short_name': 'globus'}
                       ]
                       }},
        'identity_id': 'mal-ident-1-uuid',
        'idp_id': 'ident-uuid',
        'last_name': 'Reynolds',
        'username': 'mal@globus.org'
    }


def test_without_sessions(settings, user_details):
    settings.SOCIAL_AUTH_GLOBUS_SESSIONS = False
    goidc = GlobusOpenIdConnect()
    assert goidc.auth_allowed(dict(), user_details) is True


def test_without_allowed_groups(settings, user_details):
    settings.SOCIAL_AUTH_GLOBUS_ALLOWED_GROUPS = []
    goidc = GlobusOpenIdConnect()
    assert goidc.auth_allowed(dict(), user_details) is True


def test_with_one_group(settings, mock_group_tokens, groups,
                        user_details, get_json):
    settings.SOCIAL_AUTH_GLOBUS_ALLOWED_GROUPS = [
       {'name': 'Portal Users Group',
        'uuid': 'test-group-1-uuid'}
    ]
    # mock GlobusOpenIdConnect routine to fetch groups
    get_json.return_value = groups
    goidc = GlobusOpenIdConnect()
    response = {'other_tokens': mock_group_tokens}
    assert goidc.auth_allowed(response, user_details) is True


def test_with_no_groups(settings, mock_group_tokens, user_details, get_json):
    settings.SOCIAL_AUTH_GLOBUS_ALLOWED_GROUPS = [
       {'name': 'Portal Users Group',
        'uuid': 'test-group-1-uuid'}
    ]
    # Globus returns no groups
    get_json.return_value = []
    goidc = GlobusOpenIdConnect()
    response = {'other_tokens': mock_group_tokens}
    with pytest.raises(social_core.exceptions.AuthForbidden):
        goidc.auth_allowed(response, user_details)


def test_with_wrong_identity(settings, mock_group_tokens, user_details, groups,
                             get_json):
    settings.SOCIAL_AUTH_GLOBUS_ALLOWED_GROUPS = [
       {'name': 'Portal Users Group',
        'uuid': 'test-group-1-uuid'}
    ]
    get_json.return_value = groups
    response = {'other_tokens': mock_group_tokens}
    goidc = GlobusOpenIdConnect()
    try:
        goidc.auth_allowed(response, user_details)
    except social_core.exceptions.AuthForbidden as af:
        username = af.args[0]['allowed_user_member_groups'][0]['username']
        assert username == 'mal@anl.gov'


def test_introspect(get_json):
    goidc = GlobusOpenIdConnect()
    goidc.introspect_token('mock_token')
    get_json.assert_called_with(
        'https://auth.globus.org//v2/oauth2/token/introspect',
        auth=('mock_client_id', 'mock_client_secret'),
        data={'token': 'mock_token', 'include': 'session_info,identities_set'},
        method='POST'
    )


def test_get_identities(get_json):
    goidc = GlobusOpenIdConnect()
    goidc.get_globus_identities('mock_token', ['id1, id2'])
    get_json.assert_called_with(
        'https://auth.globus.org//v2/api/identities',
        headers={'Authorization': 'Bearer mock_token'},
        method='GET',
        params={'ids': 'id1, id2', 'include': 'identity_provider'}
    )


def test_standard_get_user_id(settings, user_details):
    response = {'sub': 'mal-ident-1-uuid'}
    settings.SOCIAL_AUTH_GLOBUS_SESSIONS = False
    goidc = GlobusOpenIdConnect()
    user_id = goidc.get_user_id(user_details, response)
    assert user_id == 'mal-ident-1-uuid'


def test_sessions_get_user_id(settings, user_details):
    settings.SOCIAL_AUTH_GLOBUS_SESSIONS = True
    goidc = GlobusOpenIdConnect()
    user_id = goidc.get_user_id(user_details, dict())
    assert user_id == 'ident-uuid_mal-ident-1-uuid'
