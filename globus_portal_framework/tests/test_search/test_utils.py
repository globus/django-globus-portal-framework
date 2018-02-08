import os
from unittest import mock
from django.test import TestCase, Client
from django.test.utils import override_settings
from django.contrib.auth.models import User, AnonymousUser
from social_django.models import UserSocialAuth
from globus_portal_framework.tests.test_search import (get_mock_data,
                                                       SEARCH_SCHEMA,
                                                       MOCK_RESULT,
                                                       DEFAULT_MAPPER
                                                       )

from globus_portal_framework.search.utils import (load_search_client,
                                                  process_search_data)


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
            'extra_data': {'access_token': 'foo'}
        }
        self.soc_auth = UserSocialAuth.objects.create(**self.extra_data)
        self.real_user.provider = 'globus'

    @mock.patch('globus_sdk.SearchClient', MockSearchClient)
    def test_load_search_client(self):
        c = load_search_client(AnonymousUser())
        assert c.kwargs == {}

    @mock.patch('globus_sdk.SearchClient', MockSearchClient)
    def test_load_search_client(self):
        c = load_search_client(self.real_user)
        assert c.kwargs['authorizer']

    @override_settings(SEARCH_MAPPER=DEFAULT_MAPPER)
    @override_settings(SEARCH_SCHEMA=SEARCH_SCHEMA)
    @override_settings(SEARCH_INDEX='myindex')
    def test_process_search_data(self):
        mock_data = get_mock_data(MOCK_RESULT)
        data = process_search_data([mock_data])
        assert type(data) == list
        assert len(data) == 1
        assert data[0].get('subject')
        assert data[0].get('fields')
