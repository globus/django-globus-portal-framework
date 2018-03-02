from unittest import mock
from django.test import TestCase, Client
from django.test.utils import override_settings
from django.contrib.auth.models import AnonymousUser

from globus_portal_framework.tests.mocks import (
    MockGlobusClient, mock_user, globus_client_is_loaded_with_authorizer
)

from globus_portal_framework.transfer.utils import (
    load_transfer_client
)


class TransferUtilsTest(TestCase):

    @mock.patch('globus_sdk.TransferClient', MockGlobusClient)
    def test_load_search_client_with_anonymous_user(self):
        c = load_transfer_client(AnonymousUser())
        self.assertFalse(globus_client_is_loaded_with_authorizer(c))

    @mock.patch('globus_sdk.TransferClient', MockGlobusClient)
    def test_load_search_client_with_real_user(self):
        user = mock_user('bob', ['transfer.api.globus.org'])
        c = load_transfer_client(user)
        self.assertTrue(globus_client_is_loaded_with_authorizer(c))

    @mock.patch('globus_sdk.TransferClient', MockGlobusClient)
    def test_load_transfer_client_with_bad_token(self):
        user = mock_user('bob', ['search.api.globus.org'])
        with self.assertRaises(ValueError):
            load_transfer_client(user)
