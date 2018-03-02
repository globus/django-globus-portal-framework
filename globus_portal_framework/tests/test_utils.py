from unittest import mock
from django.test import TestCase
from django.contrib.auth.models import AnonymousUser
import globus_sdk


from globus_portal_framework.utils import load_globus_client

from globus_portal_framework.tests.mocks import (
    MockGlobusClient, mock_user, globus_client_is_loaded_with_authorizer
)


class GlobusPortalFrameworkUtilsTests(TestCase):

    @mock.patch('globus_sdk.SearchClient', MockGlobusClient)
    def test_load_search_client_with_anonymous_user(self):
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
    def test_load_transfer_client_with_bad_token(self):
        user = mock_user('bob', ['transfer.api.globus.org'])
        with self.assertRaises(ValueError):
            c = load_globus_client(user, globus_sdk.SearchClient,
                                   'search.api.globus.org')
