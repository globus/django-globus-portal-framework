from django.test import TestCase, Client
from unittest import mock
from django.test.utils import override_settings


class MockSearchGetSubject:
    data = {'content': [{'myindex': 'search_data'}]}


class SearchViewsTest(TestCase):

    def setUp(self):
        self.c = Client()

    def test_index(self):
        r = self.c.get('/')
        assert r.status_code == 200

    @override_settings(SERACH_INDEX='myindex')
    @mock.patch('globus_sdk.SearchClient.get_subject')
    def test_detail(self, get_subject):
        get_subject.returns = MockSearchGetSubject()
        r = self.c.get('/detail/myindex/mysubject')
        assert r.status_code == 200
