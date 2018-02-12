import json

from django.test import TestCase, Client
from django.test.utils import override_settings

from unittest import mock


class DjangoChecksTest(TestCase):

    @override_settings(SEARCH_SCHEMA='foo')
    def test_search_schema(self, post_search):
        pass
        # post_search.return_value = MockSearchResult()
        #
        # r = self.c.post('/api/v1/search/mdf',
        #                 content_type='application/json',
        #                 data=json.dumps({'search': 'data'})
        #                 )
        # assert r.status_code == 200
        # assert r.json() == MockSearchResult.data
