import json

from django.test import TestCase, Client
from unittest import mock


class MockSearchResult:
    data = {'results': 'search_result_data'}


class SearchAPITest(TestCase):

    def setUp(self):
        self.c = Client()

    @mock.patch('globus_sdk.SearchClient.post_search')
    def test_api(self, post_search):
        post_search.return_value = MockSearchResult()

        r = self.c.post('/api/v1/search/mdf',
                        content_type='application/json',
                        data=json.dumps({'search': 'data'})
                        )
        assert r.status_code == 200
        assert r.json() == MockSearchResult.data
