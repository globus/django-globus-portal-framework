from unittest import mock
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import AnonymousUser, User
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

import globus_sdk


from globus_portal_framework.tests.mocks import (
    mock_user, MockTransferClient, MockTransferAPIError
)

from globus_portal_framework import (
    transfer_file, parse_globus_url,
    helper_page_transfer, get_helper_page_url, check_exists, is_file
)


class TransferUtilsTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='mal', email='mal@globus.org', password='globusrocks')
        self.foo_endpoint = '3274dd6e-4d2b-4d57-a94b-b2bf1bc2fad6'
        self.bar_endpoint = 'a17459fe-04a7-4620-a831-810d7190358b'

    def globus_helper_page_request(self):
        post_data = {
            'endpoint_id': self.bar_endpoint,
            'path': '/helper_page_path',
            'label': 'my transfer'
        }
        request = self.factory.post('/transfer_stuff',
                                    data=post_data)
        request.user = self.user
        return request

    @mock.patch('globus_sdk.TransferAPIError', MockTransferAPIError)
    @mock.patch('globus_portal_framework.gtransfer.is_file')
    def test_check_exists(self, is_file):
        check_exists(self.user, self.foo_endpoint, 'path')
        self.assertTrue(is_file.called)

    @mock.patch('globus_sdk.TransferAPIError', MockTransferAPIError)
    @mock.patch('globus_sdk.TransferClient')
    def test_is_file_on_mock_file(self, tc):
        # Transfer Client raises on existing files
        tc.return_value = MockTransferClient(raise_on_ls=True)
        user = mock_user('alice', ['transfer.api.globus.org'])
        self.assertTrue(is_file(user, self.foo_endpoint, 'foo.txt'))

    @mock.patch('globus_sdk.TransferAPIError', MockTransferAPIError)
    @mock.patch('globus_sdk.TransferClient')
    def test_is_file_on_mock_dir(self, tc):
        # TC won't raise on dirs
        tc.return_value = MockTransferClient(raise_on_ls=False)
        user = mock_user('alice', ['transfer.api.globus.org'])
        self.assertFalse(is_file(user, self.foo_endpoint, 'foo/'))

    @mock.patch('globus_sdk.TransferAPIError', MockTransferAPIError)
    @mock.patch('globus_sdk.TransferClient')
    def test_is_file_raises_errors_properly(self, tc):
        # We'll assume a TransferAPIError of type FOO, the worst kind of error
        tc.return_value = MockTransferClient(raise_on_ls=True, exc_code='FOO')
        user = mock_user('alice', ['transfer.api.globus.org'])
        with self.assertRaises(globus_sdk.TransferAPIError):
            is_file(user, self.foo_endpoint, 'bar', raises=True)

        tc.return_value = MockTransferClient(raise_on_ls=True)
        # No error should be raised here, due to the exception indicating
        # the file exists
        self.assertTrue(is_file(user, self.foo_endpoint, 'bar', raises=True))

    def test_get_helper_page_url(self):
        url = get_helper_page_url('http://example.com/transfer_callback',
                                  cancel_url='http://example.com/choose_file',
                                  folder_limit=234,
                                  file_limit=934,
                                  label='bestest-transfer')
        # Check that these things are generally making it into the url. Don't
        # bother checking for URL encoded stuff.
        self.assertIn('234', url)
        self.assertIn('934', url)
        self.assertIn('bestest-transfer', url)
        self.assertIn('transfer_callback', url)
        self.assertIn('choose_file', url)
        check_url_valid = URLValidator()
        check_url_valid(url)

    def test_get_helper_page_url_raises_error_for_bad_callback(self):
        with self.assertRaises(ValidationError):
            get_helper_page_url('not_a_valid_url.com')

    def test_get_helper_page_url_raises_error_for_bad_cancel_url(self):
        with self.assertRaises(ValidationError):
            get_helper_page_url('http://example.com/transfer_callback',
                                cancel_url='you_shall_not_go_back.edu')

    @mock.patch('globus_portal_framework.gtransfer.transfer_file')
    def test_helper_page_transfer(self, transfer_file):
        request = self.globus_helper_page_request()
        helper_page_transfer(request, self.foo_endpoint, '/path',
                             helper_page_is_dest=True)
        args, kwargs = transfer_file.call_args
        u, src_ep, src_path, dest_ep, dest_path, label = args
        self.assertEqual(u, self.user)
        self.assertEqual(src_ep, self.foo_endpoint)
        self.assertEqual(src_path, '/path')
        self.assertEqual(dest_ep, self.bar_endpoint)
        self.assertEqual(dest_path, '/helper_page_path')
        self.assertEqual(label, 'my transfer')

    @mock.patch('globus_portal_framework.gtransfer.transfer_file')
    def test_helper_page_transfer_helper_page_as_source(self, transfer_file):
        request = self.globus_helper_page_request()
        helper_page_transfer(request, self.foo_endpoint, '/path',
                             helper_page_is_dest=False)
        args, kwargs = transfer_file.call_args
        # Source and dest and swapped
        _, dest_ep, dest_path, src_ep, src_path, _ = args
        self.assertEqual(src_ep, self.foo_endpoint)
        self.assertEqual(src_path, '/path')
        self.assertEqual(dest_ep, self.bar_endpoint)
        self.assertEqual(dest_path, '/helper_page_path')

    @mock.patch('globus_portal_framework.gtransfer.transfer_file')
    def test_helper_page_raises_error_for_gets(self, transfer_file):
        request = self.factory.get('/transfer_stuff')
        request.user = self.user
        with self.assertRaises(ValueError):
            helper_page_transfer(request, self.foo_endpoint, '/path')

    @mock.patch('globus_portal_framework.gtransfer.transfer_file')
    def test_helper_page_raises_error_for_anonymous_user(self, transfer_file):
        request = self.globus_helper_page_request()
        request.user = AnonymousUser
        with self.assertRaises(ValueError):
            helper_page_transfer(request, self.foo_endpoint, '/path')

    @mock.patch('globus_sdk.TransferClient')
    @mock.patch('globus_sdk.TransferData')
    @mock.patch('globus_portal_framework.gtransfer.log', mock.Mock())
    def test_transfer_file(self, tdata, tclient):
        user = mock_user('bob', ['transfer.api.globus.org'])
        transfer_file(user,
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

    # def test_preview(self):
    #     """
    #     Todo: This
    #     """
    #     pass
