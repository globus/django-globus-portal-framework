from unittest import mock
from django.test import TestCase, Client
from django.contrib.auth.models import User, AnonymousUser
from social_django.models import UserSocialAuth

from globus_portal_framework.search.utils import load_search_client


class MockSearchGetSubject:
    data = {'content': [{'myindex': 'search_data'}]}


class MockSearchClient:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class SearchViewsTest(TestCase):

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
