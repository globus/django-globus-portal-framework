from uuid import uuid4
from globus_portal_framework.constants import FILTER_TYPES
from globus_portal_framework.checks import (check_search_indexes,)


def test_valid_search_index(search_client):
    assert check_search_indexes(None) == []


def test_index_missing_uuid(settings, search_client, globus_response):
    settings.SEARCH_INDEXES = {'myindex': {'uuid': ''}}
    globus_response.data = {'id': 'foo'}
    search_client.return_value.get_index.return_value = globus_response
    r = check_search_indexes(None)
    assert len(r) == 1
    assert r[0].id == 'globus_portal_framework.settings.E001'


def test_valid_filter_types_raise_no_errors(settings):
    valid = {
        '{}-index'.format(t): {
            'uuid': str(uuid4()),
            'filter_match': t
        }
        for t in FILTER_TYPES.keys()}
    valid['null-setting'] = {'uuid': str(uuid4())}
    settings.SEARCH_INDEXES = valid
    assert check_search_indexes(None) == []


def test_invalid_filter_types_raise_error(settings):
    settings.SEARCH_INDEXES = {
        'myindex': {'uuid': 'foo', 'filter_match': 'not-valid'}
    }
    assert check_search_indexes(None)
