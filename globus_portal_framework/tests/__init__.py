from os.path import join, dirname
import json

MOCK_DETAIL_OVERVIEW = 'globus_portal_framework/data/' \
                       'mock-detail-overview.json'
SEARCH_SCHEMA = 'globus_portal_framework/data/datacite.json'
MOCK_RESULT = 'globus_portal_framework/tests/'\
                                   'data/datacite_search_result.json'
TEST_SCHEMA = join(dirname(__file__), 'data/test_schema.json')
DEFAULT_MAPPER = ('globus_portal_framework',
                  'default_search_mapper')


def get_mock_data(filename):
    with open(filename) as f:
        data = json.loads(f.read())
        return data
