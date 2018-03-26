from datetime import timedelta
from unittest import mock
from django.test import TestCase, Client
from django.test.utils import override_settings
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone

from globus_portal_framework.tests.test_search import (get_mock_data,
                                                       SEARCH_SCHEMA,
                                                       MOCK_RESULT,
                                                       DEFAULT_MAPPER,
                                                       TEST_SCHEMA,
                                                       )
from globus_portal_framework.tests.mocks import (
    MockGlobusClient, mock_user, globus_client_is_loaded_with_authorizer
)

from globus_portal_framework.search.utils import (
    load_search_client, process_search_data, default_search_mapper,
    get_pagination, get_filters)

from globus_portal_framework.exc import ExpiredGlobusToken


class MockSearchGetSubject:
    data = {'content': [{'myindex': 'search_data'}]}


class SearchUtilsTest(TestCase):

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
            c = load_search_client(user)

    @mock.patch('globus_sdk.SearchClient', MockGlobusClient)
    def test_load_search_client_with_bad_token(self):
        user = mock_user('bob', ['transfer.api.globus.org'])
        with self.assertRaises(ValueError):
            c = load_search_client(user)

    @mock.patch('globus_portal_framework.search.settings.SEARCH_SCHEMA',
                SEARCH_SCHEMA)
    @mock.patch('globus_portal_framework.search.settings.SEARCH_MAPPER',
                DEFAULT_MAPPER)
    def test_process_search_data(self):
        mock_data = get_mock_data(MOCK_RESULT)
        data = process_search_data([mock_data])
        assert type(data) == list
        assert len(data) == 1
        assert data[0].get('subject')
        assert data[0].get('fields')

    def test_default_mapper(self):
        mock_data = get_mock_data(MOCK_RESULT)
        schema = get_mock_data(TEST_SCHEMA)
        data = default_search_mapper(mock_data['content'],
                                     schema['fields'])
        self.assertEqual(sorted(list(data.keys())), ['title', 'titles'])
        self.assertEqual(sorted(data['titles'].keys()),
                         ['data', 'field_title'])

    @override_settings(RESULTS_PER_PAGE=10, MAX_PAGES=10)
    def test_pagination(self):
        self.assertEqual(get_pagination(1000, 0)['current_page'], 1)
        self.assertEqual(get_pagination(1000, 10)['current_page'], 2)
        self.assertEqual(get_pagination(1000, 20)['current_page'], 3)
        self.assertEqual(len(get_pagination(1000, 0)['pages']), 10)

    def test_get_filters(self):
        r = get_filters({'titles': ['foo']})
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0]['type'], 'match_all')

        r = get_filters({'titles': ['foo', 'bar']})
        self.assertEqual(len(r), 1)

    def test_get_facets(self):
        pass
