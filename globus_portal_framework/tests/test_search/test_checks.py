from django.test import TestCase, Client
from django.test.utils import override_settings
from globus_portal_framework.search import (search_mapper_check,
                                            search_schema_check)


def test_mapper_func(data, schema):
    """Used for testing search_mapper_check"""
    pass


class DjangoChecksTest(TestCase):

    TEST_MAPPER = ('globus_portal_framework.tests.test_search.test_checks',
                   'test_mapper_func')
    TEST_SCHEMA = 'globus_portal_framework/tests/test_search/data/' \
                  'test_schema.json'

    @override_settings(SEARCH_MAPPER=TEST_MAPPER)
    def test_mapper_with_valid_mapper(self):

        r = search_mapper_check(None)
        self.assertEquals(r, [])

    @override_settings(SEARCH_MAPPER=('does.not.exist', 'nope'))
    def test_mapper_with_invalid_mapper_returns_error(self):
        r = search_mapper_check(None)
        self.assertTrue(isinstance(r, list))
        self.assertEquals(len(r), 1)
        self.assertEquals(r[0].id, 'globus_portal_framework.search.E002')

    @override_settings(SEARCH_MAPPER=(TEST_MAPPER[0], ''))
    def test_unset_mapper_returns_error(self):
        r = search_mapper_check(None)
        self.assertTrue(isinstance(r, list))
        self.assertEquals(len(r), 1)
        self.assertEquals(r[0].id, 'globus_portal_framework.search.E002')

    @override_settings(SEARCH_SCHEMA=TEST_SCHEMA)
    def test_schema_check_with_valid_schema(self):
        r = search_schema_check(None)
        self.assertEquals(r, [])

    @override_settings(SEARCH_SCHEMA='invalid.json')
    def test_schema_check_with_nonexistent_file(self):
        r = search_schema_check(None)
        self.assertEquals(len(r), 1)
        self.assertEquals(r[0].id, 'globus_portal_framework.search.E004')
