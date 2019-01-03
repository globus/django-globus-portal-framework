from unittest import mock
from uuid import uuid4
from django.test import TestCase
from django.test.utils import override_settings
from globus_portal_framework.constants import FILTER_TYPES
from globus_portal_framework.checks import (check_search_indexes,)


# Produces four indexes with valid filter_match settings
VALID_FILTER_MATCH_SETTINGS = {
    '{}-index'.format(t): {
        'uuid': str(uuid4()),
        'filter_match': t
    }
    for t in FILTER_TYPES.keys()}
VALID_FILTER_MATCH_SETTINGS['null-setting'] = {'uuid': str(uuid4())}


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

    @override_settings(SEARCH_INDEXES=VALID_FILTER_MATCH_SETTINGS)
    def test_valid_filter_types_raise_no_errors(self):
        r = check_search_indexes(None)
        self.assertEquals(r, [])

    @override_settings(SEARCH_INDEXES={'myindex':
                       {'uuid': 'foo', 'filter_match': 'not-valid'}}
                       )
    def test_invalid_filter_types_raise_error(self):
        r = check_search_indexes(None)
        # Ensure something was raised
        self.assertNotEquals(r, [])
