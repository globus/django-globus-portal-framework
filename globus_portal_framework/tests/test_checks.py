from unittest import mock
from django.test import TestCase
from django.test.utils import override_settings
from globus_portal_framework.checks import (check_search_indexes,)


class DjangoChecksTest(TestCase):

    @mock.patch('globus_sdk.SearchClient', mock.Mock())
    @override_settings(SEARCH_INDEXES={'myindex': {'uuid': 'value'}})
    def test_valid_search_index(self):

        r = check_search_indexes(None)
        self.assertEquals(r, [])

    @mock.patch('globus_sdk.SearchClient', mock.MagicMock())
    @override_settings(SEARCH_INDEXES={'myindex': {'uuid': ''}})
    def test_index_missing_uuid(self):

        r = check_search_indexes(None)
        self.assertEquals(len(r), 1)
        self.assertEquals(r[0].id, 'globus_portal_framework.settings.E001')
