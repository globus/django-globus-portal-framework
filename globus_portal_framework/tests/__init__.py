from os.path import join, dirname
import json

BASE_DATA_PATH = join(dirname(__file__), 'data')

MOCK_DETAIL_OVERVIEW = 'globus_portal_framework/data/' \
                       'mock-detail-overview.json'
SEARCH_SCHEMA = 'globus_portal_framework/data/datacite.json'
MOCK_RESULT = join(BASE_DATA_PATH, 'datacite_search_result.json')
TEST_SCHEMA = join(BASE_DATA_PATH, 'test_schema.json')
PROCESSED_PORTAL_FACETS = join(BASE_DATA_PATH, 'processed_portal_facets.json')
DEFAULT_MAPPER = ('globus_portal_framework',
                  'default_search_mapper')


def get_mock_data(filename):
    with open(filename) as f:
        data = json.loads(f.read())
        return data
