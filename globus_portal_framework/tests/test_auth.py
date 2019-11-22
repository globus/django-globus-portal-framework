import social_core

from django.test import TestCase
from django.test.utils import override_settings
from globus_portal_framework.tests.mocks import mock_tokens
from globus_portal_framework.auth import GlobusOpenIdConnect


GROUPS = [
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


@override_settings(SOCIAL_AUTH_GLOBUS_SESSIONS=True,
                   SOCIAL_AUTH_GLOBUS_ALLOWED_GROUPS=[],
                   SOCIAL_AUTH_GLOBUS_SCOPE=[
                       'urn:globus:auth:scope:groups.api.globus.org:'
                       'view_my_groups_and_memberships'
                   ])
class SearchViewsTest(TestCase):

    def setUp(self):
        self.g_oidc = GlobusOpenIdConnect()
        self.details = {
            'username': 'mal@globusid.org',
            'email': 'mal@globus.org',
            'fullname': 'Malcolm Reynolds',
            'first_name': 'Malcolm',
            'last_name': 'Reynolds',
            'identity_id': 'mal-ident-1-uuid',
            'idp_id': 'ident-uuid',
            'identities': [],
        }
        tokens = mock_tokens(['04896e9e-b98e-437e-becd-8084b9e234a0'])
        tokens[0]['scope'] = ('urn:globus:auth:scope:groups.api.globus.org:'
                              'view_my_groups_and_memberships')
        self.response = {'other_tokens': tokens}

    @override_settings(SOCIAL_AUTH_GLOBUS_SESSIONS=False)
    def test_without_sessions(self):
        self.assertTrue(self.g_oidc.auth_allowed(self.response, self.details))

    @override_settings(SOCIAL_AUTH_GLOBUS_ALLOWED_GROUPS=[])
    def test_without_allowed_groups(self):
        self.assertTrue(self.g_oidc.auth_allowed(self.response, self.details))

    @override_settings(SOCIAL_AUTH_GLOBUS_ALLOWED_GROUPS=[
                       {'name': 'Portal Users Group',
                        'uuid': 'test-group-1-uuid'}])
    def test_with_one_group(self):
        self.g_oidc.get_json = lambda *a, **b: GROUPS
        self.assertTrue(self.g_oidc.auth_allowed(self.response, self.details))

    @override_settings(SOCIAL_AUTH_GLOBUS_ALLOWED_GROUPS=[
                       {'name': 'Portal Users Group',
                        'uuid': 'test-group-1-uuid'}])
    def test_with_no_groups(self):
        self.g_oidc.get_json = lambda *a, **b: []
        with self.assertRaises(social_core.exceptions.AuthForbidden):
            self.assertTrue(self.g_oidc.auth_allowed(self.response,
                                                     self.details))

    @override_settings(SOCIAL_AUTH_GLOBUS_ALLOWED_GROUPS=[
                       {'name': 'Portal Users Group',
                        'uuid': 'test-group-2-uuid'}])
    def test_with_wrong_identity(self):
        self.g_oidc.get_json = lambda *a, **b: GROUPS
        try:
            self.g_oidc.auth_allowed(self.response, self.details)
        except social_core.exceptions.AuthForbidden as af:
            username = af.args[0]['allowed_user_member_groups'][0]['username']
            self.assertEqual(username, 'mal@anl.gov')
