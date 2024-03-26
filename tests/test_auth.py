import pytest
import social_core
from unittest.mock import Mock

from tests.mocks import mock_tokens
from globus_portal_framework.auth import GlobusOpenIdConnect


class MockResponseEnvelope:
    def __init__(self, data=[]):
        self.data = data


@pytest.fixture
def groups():
    return MockResponseEnvelope([
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
    ])


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
        'sub': 'mal-ident-1-uuid',
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


def test_without_allowed_groups(settings, user_details):
    settings.SOCIAL_AUTH_GLOBUS_ALLOWED_GROUPS = []
    goidc = GlobusOpenIdConnect()
    assert goidc.auth_allowed(dict(), user_details) is True


def test_with_one_group(settings, mock_group_tokens, groups,
                        user_details, groups_client):
    settings.SOCIAL_AUTH_GLOBUS_ALLOWED_GROUPS = [
       {'name': 'Portal Users Group',
        'uuid': 'test-group-1-uuid'}
    ]
    groups_client.return_value.get_my_groups.return_value = groups
    goidc = GlobusOpenIdConnect()
    response = {'other_tokens': mock_group_tokens}
    assert goidc.auth_allowed(response, user_details) is True


def test_with_no_groups(settings, mock_group_tokens, user_details, groups_client):
    settings.SOCIAL_AUTH_GLOBUS_ALLOWED_GROUPS = [
       {'name': 'Portal Users Group',
        'uuid': 'test-group-1-uuid'}
    ]
    # Globus returns no groups
    groups_client.return_value.get_my_groups.return_value = MockResponseEnvelope()
    goidc = GlobusOpenIdConnect()
    response = {'other_tokens': mock_group_tokens}
    with pytest.raises(social_core.exceptions.AuthForbidden):
        goidc.auth_allowed(response, user_details)


def test_with_wrong_identity(settings, mock_group_tokens, user_details, groups,
                             groups_client):
    settings.SOCIAL_AUTH_GLOBUS_ALLOWED_GROUPS = [
       {'name': 'Portal Users Group',
        'uuid': 'test-group-1-uuid'}
    ]
    groups_client.return_value.get_my_groups.return_value = groups
    # get_json.return_value = groups
    response = {'other_tokens': mock_group_tokens}
    goidc = GlobusOpenIdConnect()
    try:
        goidc.auth_allowed(response, user_details)
    except social_core.exceptions.AuthForbidden as af:
        username = af.args[0]['allowed_user_member_groups'][0]['username']
        assert username == 'mal@anl.gov'


def test_groups_scope_not_configured(settings, user_details):
    settings.SOCIAL_AUTH_GLOBUS_ALLOWED_GROUPS = [
       {'name': 'Portal Users Group',
        'uuid': 'test-group-1-uuid'}
    ]
    goidc = GlobusOpenIdConnect()
    with pytest.raises(ValueError):
        goidc.auth_allowed({'other_tokens': {}}, user_details)


def test_get_user_id(settings, user_details):
    response = {'sub': 'mal-ident-1-uuid'}
    goidc = GlobusOpenIdConnect()
    user_id = goidc.get_user_id(user_details, response)
    assert user_id == 'mal-ident-1-uuid'


def test_denied_by_whitelist(settings, user_details, groups_client):
    settings.SOCIAL_AUTH_GLOBUS_WHITELISTED_DOMAINS = ['foo.com', 'bar.com']
    response = {'sub': 'mal-ident-1-uuid'}
    goidc = GlobusOpenIdConnect()
    assert goidc.auth_allowed(response, user_details) is False
    assert not groups_client.return_value.get_my_groups.called
