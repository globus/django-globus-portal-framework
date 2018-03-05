from unittest import mock
from django.test import TestCase, Client
from django.test.utils import override_settings
from django.contrib.auth.models import AnonymousUser

from globus_portal_framework.tests.mocks import (
    MockGlobusClient, mock_user, globus_client_is_loaded_with_authorizer
)

from globus_portal_framework.transfer.utils import (
    load_transfer_client, transfer_file, parse_globus_url, preview
)


class TransferUtilsTest(TestCase):

    def setUp(self):
        self.foo_endpoint = '3274dd6e-4d2b-4d57-a94b-b2bf1bc2fad6'
        self.bar_endpoint = 'a17459fe-04a7-4620-a831-810d7190358b'

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
        user = mock_user('alice', ['search.api.globus.org'])
        with self.assertRaises(ValueError):
            load_transfer_client(user)

    @mock.patch('globus_sdk.TransferClient')
    @mock.patch('globus_sdk.TransferData')
    def test_transfer_file(self, tdata, tclient):
        user = mock_user('bob', ['transfer.api.globus.org'])
        task = transfer_file(user,
                             self.foo_endpoint, 'mydir/file1.txt',
                             self.bar_endpoint, 'mybardir/file1.txt',
                             'My foo-bar file transfer')
        args, kwargs = tdata.call_args
        self.assertEqual(args[1:], (self.foo_endpoint, self.bar_endpoint))
        self.assertEqual(kwargs['label'], 'My foo-bar file transfer')
        self.assertEqual(kwargs['sync_level'], 'checksum')

    def test_parse_globus_url(self):
        foo_file = 'globus://{}:{}'.format(self.foo_endpoint, '/foo.txt')
        endpoint, path = parse_globus_url(foo_file)
        self.assertEqual(endpoint, self.foo_endpoint)
        self.assertEqual(path, '/foo.txt')

    def test_parse_globus_url_with_malformed_protocol_raises_value_error(self):
        foo_file = 'globulous://{}:{}'.format(self.foo_endpoint, '/foo.txt')
        with self.assertRaises(ValueError):
            parse_globus_url(foo_file)

    def test_parse_globus_url_with_malformed_path_raises_value_error(self):
        foo_file = 'globus://{}{}'.format(self.foo_endpoint, '/foo.txt')
        with self.assertRaises(ValueError):
            parse_globus_url(foo_file)

    def test_parse_globus_url_with_malformed_endpoint_raises_value_error(self):
        # cut the last character off the endpoint
        foo_file = 'globus://{}:{}'.format(self.foo_endpoint[:35], '/foo.txt')
        with self.assertRaises(ValueError):
            parse_globus_url(foo_file)
