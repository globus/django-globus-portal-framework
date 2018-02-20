from django.test import TestCase, Client
from unittest import mock
from django.test.utils import override_settings
from globus_portal_framework.tests import test_search


class MockSearchGetSubject:
    data = test_search.get_mock_data(test_search.MOCK_RESULT)


class SearchViewsTest(TestCase):

    def setUp(self):
        self.c = Client()

    def test_index(self):
        r = self.c.get('/')
        assert r.status_code == 200

    @override_settings(SEARCH_MAPPER=test_search.DEFAULT_MAPPER)
    @override_settings(SEARCH_SCHEMA=test_search.SEARCH_SCHEMA)
    @override_settings(SEARCH_INDEX='myindex')
    @mock.patch('globus_sdk.SearchClient.get_subject')
    def test_detail(self, get_subject):
        get_subject.return_value = MockSearchGetSubject()
        r = self.c.get('/detail/mysubject/')
        self.assertEqual(r.status_code, 200)

    @override_settings(SEARCH_MAPPER=test_search.DEFAULT_MAPPER)
    @override_settings(SEARCH_SCHEMA=test_search.SEARCH_SCHEMA)
    @override_settings(SEARCH_INDEX='myindex')
    @mock.patch('globus_sdk.SearchClient.get_subject')
    def test_detail_metadata(self, get_subject):
        get_subject.return_value = MockSearchGetSubject()
        r = self.c.get('/detail-metadata/mysubject/')
        self.assertEqual(r.status_code, 200)
