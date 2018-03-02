import os
import globus_sdk
from unittest import mock
from django.test import TestCase, Client
from django.test.utils import override_settings
from django.contrib.auth.models import User, AnonymousUser
from social_django.models import UserSocialAuth
from globus_portal_framework.tests.test_search import (get_mock_data,
                                                       SEARCH_SCHEMA,
                                                       MOCK_RESULT,
                                                       DEFAULT_MAPPER,
                                                       TEST_SCHEMA,
                                                       )

from globus_portal_framework.search.utils import (
    load_search_client, process_search_data, default_search_mapper,
    get_pagination, get_filters)


class MockSearchGetSubject:
    data = {'content': [{'myindex': 'search_data'}]}


class MockSearchClient:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class SearchUtilsTest(TestCase):

    def setUp(self):
        self.real_user = User.objects.create_user(username='bob')
        self.extra_data = {
            'user': self.real_user,
            'provider': 'globus',
            'extra_data': {'other_tokens': [
                {'resource_server': 'search.api.globus.org',
                 'access_token': 'foo'}
            ]}}
        self.soc_auth = UserSocialAuth.objects.create(**self.extra_data)
        self.real_user.provider = 'globus'

    @mock.patch('globus_sdk.SearchClient', MockSearchClient)
    def test_load_search_client(self):
        c = load_search_client(AnonymousUser())
        assert c.kwargs == {}

    @mock.patch('globus_sdk.SearchClient', MockSearchClient)
    def test_load_search_client(self):
        c = load_search_client(self.real_user)
        self.assertTrue(isinstance(c.kwargs['authorizer'],
                                   globus_sdk.AccessTokenAuthorizer))

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
