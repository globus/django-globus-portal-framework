from unittest import mock
from urllib.parse import quote_plus

from django.test import TestCase, Client
from django.test.utils import override_settings
from django.urls import reverse

from globus_portal_framework.tests import test_gsearch
from globus_portal_framework.tests.mocks import (
    get_logged_in_client, MockTransferClient)

from globus_portal_framework import (
    PreviewException, PreviewPermissionDenied, PreviewNotFound,
    PreviewServerError, PreviewBinaryData)

MY_ENTRY_SERVICE_VARS = {
    'globus_group': 'my_globus_group',
    'globus_http_link': 'my_globus_http_link',
    'globus_http_scope': 'my_globus_http_scope'
}


class MockSearchGetSubject:
    data = test_gsearch.get_mock_data(test_gsearch.MOCK_RESULT)


class SearchViewsTest(TestCase):

    def setUp(self):
        self.c = Client()
        self.foo_ep = 'eae9d78d-b353-4fa7-9dbe-c60d681bc783'
        # A valid subject url given our views
        self.subject_url = quote_plus('globus://{}:{}'.format(self.foo_ep,
                                                              'foo'))
        self.index = 'myindex'

    @mock.patch('globus_portal_framework.views.post_search')
    def test_index(self, post_search):
        post_search.return_value = {}
        r = self.c.get(reverse('search', args=[self.index]))
        self.assertEqual(r.status_code, 200)

    @mock.patch('globus_sdk.SearchClient.get_subject')
    @override_settings(SEARCH_MAPPER=test_gsearch.DEFAULT_MAPPER)
    def test_detail(self, get_subject):
        get_subject.return_value = MockSearchGetSubject()
        url = reverse('detail', args=[self.index, 'mysubject'])
        r = self.c.get(url)
        self.assertEqual(r.status_code, 200)

    @mock.patch('globus_sdk.SearchClient.get_subject')
    @override_settings(SEARCH_MAPPER=test_gsearch.DEFAULT_MAPPER)
    def test_detail_metadata(self, get_subject):
        get_subject.return_value = MockSearchGetSubject()
        url = reverse('detail-metadata', args=[self.index, 'mysubject'])
        r = self.c.get(url)
        self.assertEqual(r.status_code, 200)

    @mock.patch('globus_portal_framework.views.get_helper_page_url',
                mock.Mock())
    @mock.patch('globus_sdk.SearchClient.get_subject')
    @mock.patch('globus_sdk.TransferClient', MockTransferClient)
    def test_detail_transfer(self, get_subject):
        client, user = get_logged_in_client('mal', ['search.api.globus.org',
                                                    'transfer.api.globus.org'])
        get_subject.return_value = MockSearchGetSubject()
        url = reverse('detail-transfer', args=[self.index, self.subject_url])
        r = client.get(url)
        self.assertEqual(r.status_code, 200)

    @mock.patch('globus_portal_framework.views.log')
    @mock.patch('globus_portal_framework.views.preview')
    @mock.patch('globus_sdk.SearchClient.get_subject')
    @mock.patch('globus_sdk.TransferClient', MockTransferClient)
    @override_settings(ENTRY_SERVICE_VARS=MY_ENTRY_SERVICE_VARS)
    def test_detail_preview(self, get_subject, preview, log):
        preview.return_value = mock.Mock()
        client, user = get_logged_in_client('mal', ['search.api.globus.org',
                                                    'transfer.api.globus.org'])
        get_subject.return_value = MockSearchGetSubject()
        url = reverse('detail-preview', args=[self.index, self.subject_url])
        r = client.get(url)
        self.assertEqual(len(r.context['messages']), 0)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(preview.called)
        self.assertFalse(log.warning.called)

    @mock.patch('globus_portal_framework.views.log')
    @mock.patch('globus_portal_framework.views.preview')
    @mock.patch('globus_sdk.SearchClient.get_subject')
    @mock.patch('globus_sdk.TransferClient', MockTransferClient)
    @override_settings(ENTRY_SERVICE_VARS=MY_ENTRY_SERVICE_VARS)
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
            url = reverse('detail-preview',
                          args=[self.index, self.subject_url])
            r = client.get(url)
            self.assertEqual(len(r.context['messages']), 1)
            self.assertEqual(r.status_code, 200)

        # Once for each: ['UnexpectedError', 'ServerError']
        self.assertEqual(log.error.call_count, 2)
