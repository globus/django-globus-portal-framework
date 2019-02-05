# Types of filtering supported by Globus Search. Keys are accepted values in
# Globus Portal Framework, which show up in the URL. The corresponding values
# are accepted by Globus Search.
FILTER_MATCH_ALL = 'match-all'
FILTER_MATCH_ANY = 'match-any'
FILTER_RANGE = 'range'
FILTER_TYPES = {FILTER_MATCH_ALL: 'match_all',
                FILTER_MATCH_ANY: 'match_any',
                FILTER_RANGE: 'range'}
# Precompile the RE for detecting the filter type.
__f_types = '|'.join(FILTER_TYPES.keys())
FILTER_QUERY_PATTERN = '^filter(-(?P<filter_type>{}))?\\..*'.format(__f_types)
