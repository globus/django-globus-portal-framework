from unittest import mock
import json
from django.test import TestCase, Client
from django.contrib.auth.models import User, AnonymousUser
from social_django.models import UserSocialAuth

from globus_portal_framework.search.utils import (load_search_client,
                                                  map_to_datacite)


class MockSearchGetSubject:
    data = {'content': [{'myindex': 'search_data'}]}


class MockSearchClient:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


def get_mock_data():
    filename = 'globus_portal_framework/search/data/mock-detail-overview.json'
    with open(filename) as f:
        data = json.loads(f.read())
        return data


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

    def test_map_to_datacite_with_full_mock_data(self):
        mock_data = get_mock_data()
        details = map_to_datacite(mock_data)
        for name, data in details.items():
            assert data.get('value')
