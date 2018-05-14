from unittest import mock
from urllib.parse import quote_plus

from django.test import TestCase, Client
from django.test.utils import override_settings
from django.urls import reverse

from globus_sdk import TransferAPIError

from globus_portal_framework.tests import test_search
from globus_portal_framework.tests.mocks import (
    get_logged_in_client, MockTransferClient, MockTransferAPIError)

from globus_portal_framework import (
    PreviewException, PreviewPermissionDenied, PreviewNotFound,
    PreviewServerError, PreviewBinaryData)

MY_ENTRY_SERVICE_VARS = {
    'globus_group': 'my_globus_group',
    'globus_http_link': 'my_globus_http_link',
    'globus_http_scope': 'my_globus_http_scope'
}


class MockSearchGetSubject:
    data = test_search.get_mock_data(test_search.MOCK_RESULT)


class SearchViewsTest(TestCase):

    def setUp(self):
        self.c = Client()
        self.foo_ep = 'eae9d78d-b353-4fa7-9dbe-c60d681bc783'
        # A valid subject url given our views
        self.subject_url = quote_plus('globus://{}:{}'.format(self.foo_ep,
                                                              'foo'))

    def test_index(self):
        r = self.c.get('/')
        self.assertEqual(r.status_code, 200)

    @mock.patch('globus_portal_framework.search.settings.SEARCH_MAPPER',
                test_search.DEFAULT_MAPPER)
    @mock.patch('globus_sdk.SearchClient.get_subject')
    def test_detail(self, get_subject):
        get_subject.return_value = MockSearchGetSubject()
        r = self.c.get(reverse('detail', args=['mysubject']))
        self.assertEqual(r.status_code, 200)

    @mock.patch('globus_portal_framework.search.settings.SEARCH_MAPPER',
                test_search.DEFAULT_MAPPER)
    @mock.patch('globus_sdk.SearchClient.get_subject')
    def test_detail_metadata(self, get_subject):
        get_subject.return_value = MockSearchGetSubject()
        r = self.c.get(reverse('detail-metadata', args=['mysubject']))
        self.assertEqual(r.status_code, 200)

    @mock.patch('globus_portal_framework.search.views.get_helper_page_url',
                mock.Mock())
    @mock.patch('globus_sdk.SearchClient.get_subject')
    @mock.patch('globus_sdk.TransferClient', MockTransferClient)
    def test_detail_transfer(self, get_subject):
        client, user = get_logged_in_client('mal', ['search.api.globus.org',
                                                    'transfer.api.globus.org'])
        get_subject.return_value = MockSearchGetSubject()
        r = client.get(reverse('detail-transfer', args=[self.subject_url]))
        self.assertEqual(r.status_code, 200)

    @mock.patch('globus_portal_framework.search.views.log')
    @mock.patch('globus_portal_framework.search.views.preview')
    @mock.patch('globus_sdk.SearchClient.get_subject')
    @mock.patch('globus_sdk.TransferClient', MockTransferClient)
    @mock.patch('globus_portal_framework.search.views.t_settings.'
                'ENTRY_SERVICE_VARS', MY_ENTRY_SERVICE_VARS)
    @mock.patch('globus_portal_framework.search.utils.t_settings.'
                'ENTRY_SERVICE_VARS', MY_ENTRY_SERVICE_VARS)
    def test_detail_preview(self, get_subject, preview, log):
        preview.return_value = mock.Mock()
        client, user = get_logged_in_client('mal', ['search.api.globus.org',
                                                    'transfer.api.globus.org'])
        get_subject.return_value = MockSearchGetSubject()
        r = client.get(reverse('detail-preview', args=[self.subject_url]))
        self.assertEqual(len(r.context['messages']), 0)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(preview.called)
        self.assertFalse(log.warning.called)

    @mock.patch('globus_portal_framework.search.views.log')
    @mock.patch('globus_portal_framework.search.views.preview')
    @mock.patch('globus_sdk.SearchClient.get_subject')
    @mock.patch('globus_sdk.TransferClient', MockTransferClient)
    @mock.patch('globus_portal_framework.search.views.t_settings.'
                'ENTRY_SERVICE_VARS', MY_ENTRY_SERVICE_VARS)
    @mock.patch('globus_portal_framework.search.utils.t_settings.'
                'ENTRY_SERVICE_VARS', MY_ENTRY_SERVICE_VARS)
    def test_detail_preview_exceptions(self, get_subject, preview, log):
        client, user = get_logged_in_client('mal', ['search.api.globus.org',
                                                    'transfer.api.globus.org'])
        get_subject.return_value = MockSearchGetSubject()
        excs = (PreviewException, PreviewPermissionDenied, PreviewNotFound,
                PreviewServerError, PreviewBinaryData)
        for exc in excs:
            if exc == PreviewServerError:
                preview.side_effect = PreviewServerError(500, 'Serv Err')
            else:
                preview.side_effect = exc
            r = client.get(reverse('detail-preview', args=[self.subject_url]))
            self.assertEqual(len(r.context['messages']), 1)
            self.assertEqual(r.status_code, 200)

        # Once for each: ['UnexpectedError', 'ServerError']
        self.assertEqual(log.error.call_count, 2)
