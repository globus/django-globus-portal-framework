from unittest import mock
import requests
import pytest

from django.urls import reverse, path
from django.urls.exceptions import NoReverseMatch
from django.views.defaults import server_error

from globus_portal_framework.urls import urlpatterns

urlpatterns += [
    path('exception-view/', server_error),
]


def test_search_basic(client, mock_data_search):
    r = client.get(reverse('search', args=['testindex']))
    assert r.status_code == 200


def test_nonexistant_search_index(client):
    with pytest.raises(NoReverseMatch):
        client.get(reverse('search', args=['index-does-not-exist']))


def test_detail(client, mock_data_get_subject):
    url = reverse('detail', args=['testindex', 'mysubject'])
    r = client.get(url)
    assert r.status_code == 200

# @mock.patch('globus_portal_framework.views.base.log')
# @mock.patch('globus_portal_framework.views.base.get_helper_page_url',
#             mock.Mock())
# @mock.patch('globus_sdk.SearchClient.get_subject')
# @mock.patch('globus_sdk.TransferClient', MockTransferClient)
# def test_detail_transfer_no_field_rfm(self, get_subject, log):
#     client, user = get_logged_in_client('mal', ['search.api.globus.org',
#                                                 'transfer.api.globus.org'])
#     get_subject.return_value = MockSearchGetSubject()
#     url = reverse('detail-transfer', args=[self.index, self.subject_url])
#     r = client.get(url)
#     self.assertTrue(log.error.called)
#     self.assertEqual(r.status_code, 200)
#
# @mock.patch('globus_portal_framework.views.base.log')
# @mock.patch('globus_portal_framework.views.base.get_helper_page_url',
#             mock.Mock())
# @mock.patch('globus_sdk.SearchClient.get_subject')
# @mock.patch('globus_sdk.TransferClient', MockTransferClient)
# @override_settings(SEARCH_INDEXES=SEARCH_INDEXES_TRANSFER)
# def test_detail_transfer_no_search_rfm(self, get_subject, log):
#     client, user = get_logged_in_client('mal', ['search.api.globus.org',
#                                                 'transfer.api.globus.org'])
#     get_subject.return_value = MockSearchGetSubject()
#     url = reverse('detail-transfer', args=[self.index, self.subject_url])
#     r = client.get(url)
#     self.assertTrue(log.error.called)
#     self.assertEqual(r.status_code, 200)
#
# @mock.patch('globus_portal_framework.views.base.log')
# @mock.patch('globus_portal_framework.views.base.get_helper_page_url',
#             mock.Mock())
# @mock.patch('globus_sdk.SearchClient.get_subject')
# @mock.patch('globus_sdk.TransferClient', MockTransferClient)
# @override_settings(SEARCH_INDEXES=SEARCH_INDEXES_TRANSFER)
# def test_detail_transfer_setup_correctly(self, get_subject, log):
#     client, user = get_logged_in_client('mal', ['search.api.globus.org',
#                                                 'transfer.api.globus.org'])
#     mock_search = MockSearchGetSubject()
#     mock_search.data['content'][0]['remote_file_manifest'] = MOCK_RFM
#     get_subject.return_value = mock_search
#     url = reverse('detail-transfer', args=[self.index, self.subject_url])
#     r = client.get(url)
#     self.assertFalse(log.error.called)
#     self.assertEqual(r.status_code, 200)
#
# @mock.patch('globus_portal_framework.views.base.log')
# @mock.patch('globus_portal_framework.views.base.preview')
# @mock.patch('globus_sdk.SearchClient.get_subject')
# @mock.patch('globus_sdk.TransferClient', MockTransferClient)
# def test_detail_preview(self, get_subject, preview, log):
#     preview.return_value = mock.Mock()
#     client, user = get_logged_in_client('mal', ['search.api.globus.org',
#                                                 'transfer.api.globus.org'])
#     get_subject.return_value = MockSearchGetSubject()
#     url = reverse('detail-preview', args=[self.index, self.subject_url,
#                                           self.foo_ep, 'bar'],
#                   )
#     r = client.get(url)
#     self.assertEqual(len(r.context['messages']), 0)
#     self.assertEqual(r.status_code, 200)
#     self.assertFalse(log.warning.called)
#     self.assertTrue(preview.called)
#
# @mock.patch('globus_portal_framework.views.base.log')
# @mock.patch('globus_portal_framework.views.base.preview')
# @mock.patch('globus_sdk.SearchClient.get_subject')
# @mock.patch('globus_sdk.TransferClient', MockTransferClient)
# def test_detail_preview_exceptions(self, get_subject, preview, log):
#     client, user = get_logged_in_client('mal', ['search.api.globus.org',
#                                                 'transfer.api.globus.org'])
#     get_subject.return_value = MockSearchGetSubject()
#     excs = (PreviewException, PreviewPermissionDenied, PreviewNotFound,
#             PreviewServerError, PreviewBinaryData)
#     for exc in excs:
#         if exc == PreviewServerError:
#             preview.side_effect = PreviewServerError(500, 'Serv Err')
#         else:
#             preview.side_effect = exc
#         url = reverse('detail-preview',
#                       args=[self.index, self.subject_url, self.foo_ep,
#                             'bar'])
#         r = client.get(url)
#         self.assertEqual(r.status_code, 200)
#
#     # Once for each: ['UnexpectedError', 'ServerError']
#     self.assertEqual(log.exception.call_count, 2)
#


def test_search_debug(client, mock_data_search):
    r = client.get(reverse('search-debug', args=['testindex']))
    assert r.status_code == 200


def test_search_debug_detail(client, mock_data_get_subject):
    url = reverse('search-debug-detail', args=['testindex', 'mysubject'])
    r = client.get(url)
    assert r.status_code == 200


@pytest.mark.django_db
def test_logout(user, client, mock_app):
    client.force_login(user)
    r = client.get(reverse('logout'))
    assert user.is_authenticated
    assert r.status_code == 302
    assert mock_app.return_value.oauth2_revoke_token.called


# @mock.patch('globus_portal_framework.views.base.log', mock.Mock())
def test_404_handler(client):
    response = client.get('/not-a-real-page/')
    # Make assertions on the response here. For example:
    assert response.status_code == 404
    assert 'This page doesn\'t exist.' in response.content.decode('utf-8')


@pytest.mark.urls('tests.test_views')
def test_500_handler(client, settings):
    # settings.DEBUG = False
    response = client.get('/exception-view/')
    assert response.status_code == 500
    assert 'That\'s an error.' in response.content.decode('utf-8')


def test_allowed_groups(client):
    r = client.get(reverse('allowed-groups'))
    assert r.status_code == 200


@pytest.mark.django_db
def test_allowed_groups_with_user(user, client, monkeypatch):
    get = mock.Mock()
    get.return_value.json.return_value = []
    monkeypatch.setattr(requests, 'get', get)
    client.force_login(user)
    r = client.get(reverse('allowed-groups'))
    assert r.status_code == 200
