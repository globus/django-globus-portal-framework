from uuid import uuid4
import pytest
from globus_portal_framework.constants import FILTER_TYPES, VALID_SEARCH_VERSIONS
from globus_portal_framework.checks import (
    check_search_indexes,
    check_search_index_version,
    check_allowed_groups,
)


def test_valid_search_index(search_client):
    assert check_search_indexes(None) == []


def test_index_missing_uuid(settings, search_client, globus_response):
    settings.SEARCH_INDEXES = {'myindex': {'uuid': ''}}
    globus_response.data = {'id': 'foo'}
    search_client.return_value.get_index.return_value = globus_response
    r = check_search_indexes(None)
    assert len(r) == 1
    assert r[0].id == 'globus_portal_framework.settings.E001'



@pytest.mark.parametrize("version", VALID_SEARCH_VERSIONS)
def test_check_search_index_valid_versions(settings, version):
    settings.SEARCH_INDEXES = {'myindex': {'uuid': 'foo', '@version': version}}
    r = check_search_index_version(None)
    assert len(r) == 0


def test_check_search_index_version(settings):
    settings.SEARCH_INDEXES = {'myindex': {'uuid': 'foo', '@version': 'bar'}}
    r = check_search_index_version(None)
    assert len(r) == 1
    assert r[0].id == 'globus_portal_framework.settings.E006'


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


def test_allowed_groups_no_groups(settings):
    settings.SOCIAL_AUTH_GLOBUS_ALLOWED_GROUPS = []
    assert check_allowed_groups(None) == []


def test_allowed_groups_valid_groups(settings):
    settings.SOCIAL_AUTH_GLOBUS_ALLOWED_GROUPS = [
        {
            'uuid': '91087626-8ff6-49f4-a85d-46bb51e94ec5',
            'name': 'test_group',
        }
    ]
    assert check_allowed_groups(None) == []


def test_allowed_groups_invalid_groups(settings):
    settings.SOCIAL_AUTH_GLOBUS_ALLOWED_GROUPS = {'uuid': 'aoeu'}
    errors = check_allowed_groups(None)
    assert errors
    assert errors[0].id == 'globus_portal_framework.settings.E002'


def test_allowed_groups_malformed(settings):
    settings.SOCIAL_AUTH_GLOBUS_ALLOWED_GROUPS = [
        {
            'name': 'test_group',
        },
        {
            'uuid': '91087626-8ff6-49f4-a85d-46bb51e94ec5',
        },
        {},
    ]
    errors = check_allowed_groups(None)
    # no uuid in first group
    # no name in second group
    # neither in last group
    assert len(errors) == 4
    # Make sure they're all the same attr errors
    error = {e.id for e in errors}
    assert len(error) == 1
    assert list(error)[0] == 'globus_portal_framework.settings.E003'


def test_allowed_groups_bad_uuid(settings):
    settings.SOCIAL_AUTH_GLOBUS_ALLOWED_GROUPS = [
        {
            'uuid': '91087626-8ff6-49f4-a85d-46bb51e94ec',
            'name': 'my test group'
        },
    ]
    errors = check_allowed_groups(None)
    assert errors
    assert errors[0].id == 'globus_portal_framework.settings.E004'
