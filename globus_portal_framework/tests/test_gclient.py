from unittest import mock
from datetime import timedelta
import requests

from django.test import TestCase
from django.test.utils import override_settings
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone

import globus_sdk

from globus_portal_framework import (
    load_globus_client, load_search_client, load_transfer_client,

    ExpiredGlobusToken, GroupsException,
)

from globus_portal_framework.gclients import (
    revoke_globus_tokens, get_user_groups
)

from globus_portal_framework.tests.mocks import (
    MockGlobusClient, mock_user, globus_client_is_loaded_with_authorizer,
    get_logged_in_client,
)


class GlobusPortalFrameworkUtilsTests(TestCase):

    @mock.patch('globus_sdk.SearchClient', MockGlobusClient)
    def test_load_globus_client_with_anonymous_user(self):
        c = load_globus_client(AnonymousUser(), globus_sdk.SearchClient,
                               'search.api.globus.org')
        self.assertFalse(globus_client_is_loaded_with_authorizer(c))

    @mock.patch('globus_sdk.SearchClient', MockGlobusClient)
    def test_load_globus_client_with_real_user(self):
        user = mock_user('bob', ['search.api.globus.org'])
        c = load_globus_client(user, globus_sdk.SearchClient,
                               'search.api.globus.org')
        self.assertTrue(globus_client_is_loaded_with_authorizer(c))

    @mock.patch('globus_sdk.SearchClient', MockGlobusClient)
    def test_load_globus_client_with_bad_token(self):
        user = mock_user('bob', ['transfer.api.globus.org'])
        with self.assertRaises(ValueError):
            load_globus_client(user, globus_sdk.SearchClient,
                               'search.api.globus.org')

    @mock.patch('globus_sdk.SearchClient', MockGlobusClient)
    def test_load_search_client_with_anonymous_user(self):
        c = load_search_client(AnonymousUser())
        self.assertFalse(globus_client_is_loaded_with_authorizer(c))

    @mock.patch('globus_sdk.SearchClient', MockGlobusClient)
    def test_load_search_client_with_real_user(self):
        user = mock_user('bob', ['search.api.globus.org'])
        c = load_search_client(user)
        self.assertTrue(globus_client_is_loaded_with_authorizer(c))

    @mock.patch('globus_sdk.SearchClient', MockGlobusClient)
    @override_settings(SESSION_COOKIE_AGE=9999999999)
    def test_load_search_client_expired_tokens_raises_exception(self):
        user = mock_user('bob', ['search.api.globus.org'])
        user.last_login = timezone.now() - timedelta(days=3)
        user.save()
        with self.assertRaises(ExpiredGlobusToken):
            load_search_client(user)

    @mock.patch('globus_sdk.SearchClient', MockGlobusClient)
    def test_load_search_client_with_bad_token(self):
        user = mock_user('bob', ['transfer.api.globus.org'])
        with self.assertRaises(ValueError):
            load_search_client(user)

    @mock.patch('globus_sdk.TransferClient', MockGlobusClient)
    def test_load_transfer_client_with_anonymous_user(self):
        c = load_transfer_client(AnonymousUser())
        self.assertFalse(globus_client_is_loaded_with_authorizer(c))

    @mock.patch('globus_sdk.TransferClient', MockGlobusClient)
    def test_load_transfer_client_with_real_user(self):
        user = mock_user('bob', ['transfer.api.globus.org'])
        c = load_transfer_client(user)
        self.assertTrue(globus_client_is_loaded_with_authorizer(c))

    @mock.patch('globus_sdk.TransferClient', MockGlobusClient)
    def test_load_transfer_client_with_bad_token(self):
        user = mock_user('alice', ['search.api.globus.org'])
        with self.assertRaises(ValueError):
            load_transfer_client(user)

    @mock.patch('globus_portal_framework.gclients.log')
    @mock.patch('globus_sdk.ConfidentialAppAuthClient')
    def test_logout_revokes_tokens(self, patched_cc_client, log):
        cc_instance = mock.Mock()
        patched_cc_client.return_value = cc_instance
        user = mock_user('alice', ['auth.globus.org', 'search.api.globus.org'
                                   'transfer.api.globus.org'])
        revoke_globus_tokens(user)
        # Twice for each service access_token, and refresh_token
        self.assertEqual(cc_instance.oauth2_revoke_token.call_count, 6)

    @mock.patch('globus_portal_framework.gclients.log')
    @mock.patch('globus_sdk.ConfidentialAppAuthClient')
    @mock.patch('globus_sdk.exc')
    def test_revocation_globus_err(self, globus_exceptions, patched_cc_client,
                                   log):
        cc_instance = mock.Mock()
        patched_cc_client.return_value = cc_instance
        globus_exceptions.GlobusAPIError = Exception
        cc_instance.oauth2_revoke_token.side_effect = \
            globus_sdk.exc.GlobusAPIError

        user = mock_user('alice', ['auth.globus.org', 'search.api.globus.org'
                                   'transfer.api.globus.org'])
        revoke_globus_tokens(user)
        # Twice for each service access_token, and refresh_token
        self.assertEqual(log.exception.call_count, 3)

    @mock.patch('requests.get')
    def test_get_groups_old_token_name(self, rget):
        # get user with public groups scope
        client, user = get_logged_in_client('mal', ['04896e9e-b98e-437e-'
                                                    'becd-8084b9e234a0'])
        get_user_groups(user)
        self.assertTrue(user.is_authenticated)
        self.assertTrue(rget.called)
        self.assertTrue(rget.return_value.json.called)

    @mock.patch('requests.get')
    def test_get_groups_token_name(self, rget):
        # get user with public groups scope
        client, user = get_logged_in_client('mal',
                                            ['groups.api.globus.org'])
        get_user_groups(user)
        self.assertTrue(user.is_authenticated)
        self.assertTrue(rget.called)
        self.assertTrue(rget.return_value.json.called)

    @mock.patch('requests.get')
    def test_get_groups_bad_token_name(self, rget):
        # get user with public groups scope
        client, user = get_logged_in_client('mal',
                                            ['incorrect.api.globus.org'])
        with self.assertRaises(ValueError):
            get_user_groups(user)

    @mock.patch('requests.get')
    def test_get_groups_err_response(self, rget):
        # get user with public groups scope
        client, user = get_logged_in_client('mal', ['groups.api.globus.org'])
        rget.return_value.raise_for_status.side_effect = requests.HTTPError()
        with self.assertRaises(GroupsException):
            get_user_groups(user)
