# Types of filtering supported by Globus Search. Keys are accepted values in
# Globus Portal Framework, which show up in the URL. The corresponding values
# are accepted by Globus Search.
FILTER_MATCH_ALL = 'match-all'
FILTER_MATCH_ANY = 'match-any'
FILTER_RANGE = 'range'
FILTER_YEAR = 'year'
FILTER_MONTH = 'month'
FILTER_DAY = 'day'
FILTER_DEFAULT_RANGE_SEPARATOR = '--'
FILTER_PREFIX = 'filter'
FILTER_TYPES = {
    FILTER_MATCH_ALL: 'match_all',
    FILTER_MATCH_ANY: 'match_any',
    FILTER_RANGE: 'range',
    FILTER_YEAR: 'range',
    FILTER_MONTH: 'range',
    FILTER_DAY: 'range',
}
FILTER_DATE_RANGES = [
    FILTER_YEAR,
    FILTER_MONTH,
    FILTER_DAY,
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
