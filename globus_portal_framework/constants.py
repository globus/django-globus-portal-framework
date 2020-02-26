# Types of filtering supported by Globus Search. Keys are accepted values in
# Globus Portal Framework, which show up in the URL. The corresponding values
# are accepted by Globus Search.
FILTER_MATCH_ALL = 'match-all'
FILTER_MATCH_ANY = 'match-any'
FILTER_RANGE = 'range'
FILTER_YEAR = 'year'
FILTER_MONTH = 'month'
FILTER_DAY = 'day'
FILTER_HOUR = 'hour'
FILTER_MINUTE = 'minute'
FILTER_SECOND = 'second'
FILTER_DEFAULT_RANGE_SEPARATOR = '--'
FILTER_PREFIX = 'filter'
FILTER_TYPES = {
    FILTER_MATCH_ALL: 'match_all',
    FILTER_MATCH_ANY: 'match_any',
    FILTER_RANGE: 'range',
    FILTER_YEAR: 'range',
    FILTER_MONTH: 'range',
    FILTER_DAY: 'range',
    FILTER_HOUR: 'range',
    FILTER_MINUTE: 'range',
    FILTER_SECOND: 'range',
}
FILTER_DATE_RANGES = [
    FILTER_YEAR,
    FILTER_MONTH,
    FILTER_DAY,
    FILTER_HOUR,
    FILTER_MINUTE,
    FILTER_SECOND,
]
# Precompile the RE for detecting the filter type.
__f_types = '|'.join(FILTER_TYPES.keys())
FILTER_QUERY_PATTERN = '^{}(-(?P<filter_type>{}))?\\..*'.format(
    FILTER_PREFIX, __f_types)

FILTER_DATE_TYPE_PATTERN = (
    r'(?P<year>\d\d\d\d)'
    r'(?P<month>-\d\d)?'
    r'(?P<day>-\d\d)?'
    r'(?P<time> \d\d:\d\d:\d\d)?'
)

DATETIME_PARTIAL_FORMATS = {
    'year': '%Y',
    'month': '%Y-%m',
    'day': '%Y-%m-%d',
    'time': '%Y-%m-%d %H:%M:%S'
}

VALID_SEARCH_KEYS = [
    'q', 'limit', 'offset', 'facets', 'filters', 'boosts', 'sort',
    'query_template', 'advanced', 'bypass_visible_to', 'result_format_version',
]

VALID_SEARCH_FACET_KEYS = [
    'name', 'type', 'field_name', 'size', 'histogram_range', 'date_interval'
]
# https://docs.globus.org/api/search/search/#request_documents
SRF_2017_09_01 = '2017-09-01'
SRF_2019_08_27 = '2019-08-27'
DEFAULT_RESULT_FORMAT_VERSION = SRF_2017_09_01
