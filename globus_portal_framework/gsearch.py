from __future__ import division
import os
import re
import json
import logging
import math
import collections
import datetime
from urllib.parse import quote_plus, unquote
import globus_sdk
from django import template
from django.conf import settings

from globus_portal_framework.apps import get_setting
from globus_portal_framework import load_search_client, IndexNotFound, exc
from globus_portal_framework.constants import (
    FILTER_QUERY_PATTERN, FILTER_TYPES, FILTER_RANGE, FILTER_MATCH_ALL,
    FILTER_MATCH_ANY, FILTER_DATE_RANGES, FILTER_DEFAULT_RANGE_SEPARATOR,
    FILTER_DATE_TYPE_PATTERN, DATETIME_PARTIAL_FORMATS,
)
FILTER_RANGE_SEPARATOR = getattr(settings, 'FILTER_RANGE_SEPARATOR',
                                 FILTER_DEFAULT_RANGE_SEPARATOR)


log = logging.getLogger(__name__)
filter_query_matcher = re.compile(FILTER_QUERY_PATTERN)
filter_date_matcher = re.compile(FILTER_DATE_TYPE_PATTERN)


def post_search(index, query, filters, user=None, page=1):
    """Perform a search and return the relevant data for display to the user.
    Returns a dict with search info stripped, containing only two relevant
    fields:

    {
        'search_results': [{'title': 'My title'...} ...],
        'facets': [{
            '@datatype': 'GFacetResult',
            '@version': '2017-09-01',
            'buckets': [{'@datatype': 'GBucket',
               '@version': '2017-09-01',
               'count': 1310,
               'field_name': 'mdf.resource_type',
               'value': 'record'},
              {'@datatype': 'GBucket',
               '@version': '2017-09-01',
               'count': 4,
               'field_name': 'mdf.resource_type',
               'value': 'dataset'}],
            }, ...]
    }

    See Search docs here:
    https://docs.globus.org/api/search/schemas/GSearchRequest/
    """
    if not index or not query:
        return {'search_results': [], 'facets': []}

    client = load_search_client(user)
    index_data = get_index(index)
    search_data = {
        'q': query,
        'facets': prepare_search_facets(index_data.get('facets', [])),
        'filters': filters,
        'offset': (int(page) - 1) * get_setting('SEARCH_RESULTS_PER_PAGE'),
        'limit': get_setting('SEARCH_RESULTS_PER_PAGE')
    }
    try:
        result = client.post_search(index_data['uuid'], search_data)
        return {
            'search_results': process_search_data(index_data.get('fields', []),
                                                  result.data['gmeta']),
            'facets': get_facets(result, index_data.get('facets', []),
                                 filters, index_data.get('filter_match')),
            'pagination': get_pagination(result.data['total'],
                                         result.data['offset']),
            'count': result.data['count'],
            'offset': result.data['offset'],
            'total': result.data['total'],
            }
    except globus_sdk.exc.SearchAPIError as sapie:
        log.exception(sapie)
        etext = ('There was an error in {}, you can file '
                 'an issue here:\n{}\nWith the following data: \n\n')
        gs = 'https://github.com/globusonline/globus-search/issues'
        dgpf = 'https://github.com/globusonline/django-globus-portal-framework'
        if str(sapie.http_status).startswith('5'):
            error = etext.format('Globus Search', gs)
        else:
            error = etext.format('Globus Portal Framework', dgpf)
        full_error = '{}Index ID: {}\nAuthenticated? {}\nParams: \n{}'.format(
            error, index_data['uuid'], user.is_authenticated,
            json.dumps(search_data, indent=2)
        )
        log.error(full_error)
    return {'error': 'There was an error in your search, please try a '
            'different query or contact your administrator.'}


def get_search_query(request):
    """Get the search query from the request, or fall back on the user's last
    search. If neither of those exist, settings.DEFAULT_QUERY is used instead.
    """
    return (request.GET.get('q') or request.session.get('query') or
            get_setting('DEFAULT_QUERY'))


def get_search_filters(
        request,
        filter_match_default=get_setting('DEFAULT_FILTER_MATCH'),
        index=None):
    """Given a request, fetch all query params for filters and return a list
    that can be sent to Globus Search. Filter types are
    parsed from the following keys:
        * filter.<field_name>
        * filter-match-all.<field_name>
        * filter-match-any.<field_name>
        * filter-range.<field_name>

    `filter.` will fall back on a match default defined in settings.
    `filter_match_default` can be "match-any" or "match-all"

    """
    filters = []
    for key in request.GET.keys():
        match = filter_query_matcher.match(key)
        if match:
            filter_type = match.groupdict().get('filter_type')
            # Prefix was used to determine type and can be discarded. If we got
            # here, a format match was detected and we can split on first '.'
            _, filter_name = key.split('.', maxsplit=1)
            filters.append({
                'field_name': filter_name,
                'type': (FILTER_TYPES.get(filter_type) or
                         FILTER_TYPES.get(filter_match_default)),
                'values': parse_filters(request.GET.getlist(key), filter_type)
            })

    # Need to do post processing on facets
    # Filters need to know the resolution of the facet filter

    # Facets need to know the range of filtering being used
    return filters


def parse_filters(filter_values, filter_type):
    """
    Parse raw filters and return a list of parsed filter values. The resulting
    parsed list will contain info for:s
    """
    if filter_type in [FILTER_MATCH_ANY, FILTER_MATCH_ALL]:
        return list(filter_values)
    if filter_type in FILTER_DATE_RANGES:
        # TODO: This is a SUPER hacky way to define the date intervals for
        # constructing a search. A better way would be to zero the amount of
        # time. That way we don't run into problems where dates bleed into one
        # another. For example a date facet 2019-12-20 will match yesterday if
        # yesterdays time was 11pm.
        intervals = {
            'day': datetime.timedelta(days=1),
            'month': datetime.timedelta(days=29),
            'year': datetime.timedelta(days=365)
        }
        date_pattern = DATETIME_PARTIAL_FORMATS.get(filter_type)
        interval_val = intervals[filter_type]
        return [{
                'from': (parse_date_filter(dt)['datetime'] - interval_val)
                .strftime(date_pattern),
                'to': (parse_date_filter(dt)['datetime'] + interval_val)
                .strftime(date_pattern)
                } for dt in filter_values]
    if filter_type == FILTER_RANGE:
        parsed_filters = []
        for v in filter_values:
            try:
                new_filter = deserialize_gsearch_range(v)
                if new_filter:
                    parsed_filters.append(new_filter)
            except exc.InvalidRangeFilter as irf:
                log.debug(irf)
                continue
            except Exception as e:
                log.exception(e)
                continue
        return parsed_filters


def get_search_filter_query_key(field_name,
                                filter_type=get_setting('DEFAULT_FILTER_MATCH')
                                ):
    """Create the key for a query parameter that will be recognized by
    Globus Portal Framework.
    `field_name` is the field in Globus Search to filter against.
    `filter_type` is the filter to apply. range filter MUST be 'range'. Match
    filter can be either be match-all or match-any, with DEFAULT_FILTER_MATCH
    being used if not specified."""
    if filter_type not in FILTER_TYPES:
        log.warning('{} got {}, must be one of {}. Using default...'.format(
            field_name, filter_type, list(FILTER_TYPES.keys())))
    return 'filter-{}.{}'.format(filter_type, field_name)


def prepare_search_facets(facets):
    for facet in facets:
        if not isinstance(facet, dict):
            raise ValueError('Each facet must be of type "dict"')
        if not facet.get('field_name'):
            raise ValueError('Each facet must define at minimum "field_name"')
        facet['name'] = facet.get('name', facet['field_name'])
        facet['type'] = facet.get('type', 'terms')
        facet['size'] = facet.get('size', 10)
    return facets


def get_template(index, base_template):
    """If a user has defined a custom template for visualizing search data for
    their index, load that template. Otherwise, load the default template.

    NOTE: Template paths are relative to django TEMPLATES in settings.py, """
    template_override = base_template
    try:
        idata = get_index(index)
        base_dir = idata.get('template_override_dir', '')
        to = os.path.join(base_dir, base_template)
        # Raises exception
        template.loader.get_template(to)
        template_override = to
    except template.TemplateDoesNotExist:
        pass
    except Exception as e:
        log.exception(e)
    return template_override


def get_index(index):
    """
    Get an index given an index index url. A 'url' is a short name used
    to refer to a search index through the globus_portal_framework, and does
    not represent the real index name or its UUID.
    :param index:
    :return: all data about the index or raises
    """
    indexes = get_setting('SEARCH_INDEXES') or {}
    data = indexes.get(index, None)
    if data is None:
        raise IndexNotFound(index)
    return data


def get_subject(index, subject, user=None):
    """Get a subject and run the result through the SEARCH_MAPPER defined
    in settings.py. If no subject exists, return context with the 'subject'
    and an 'error' message."""
    client = load_search_client(user)
    try:
        idata = get_index(index)
        result = client.get_subject(idata['uuid'], unquote(subject))
        return process_search_data(idata.get('fields', {}), [result.data])[0]
    except globus_sdk.exc.SearchAPIError:
        return {'subject': subject, 'error': 'No data was found for subject'}


def process_search_data(field_mappers, results):
    """
    Process results in a general search result, running the mapping function
    for each result and preparing other general data for being shown in
    templates (such as quoting the subject and including the index).
    :param results: List of GMeta results, which would be the r.data['gmeta']
    in from a simple query to Globus Search. See here:
    https://docs.globus.org/api/search/schemas/GMetaResult/
    :return: A list of search results:


    """
    structured_results = []
    for entry in results:
        content = entry['content']
        result = {
            'subject': quote_plus(entry['subject']),
            'all': content
        }

        if len(content) == 0:
            log.warning('Subject {} contained no content, skipping...'.format(
                entry['subject']
            ))
            continue
        default_content = content[0]

        for mapper in field_mappers:
            field = {}
            if isinstance(mapper, str):
                field = {mapper: default_content.get(mapper)}
            elif isinstance(mapper, collections.Iterable) and len(mapper) == 2:
                field_name, map_approach = mapper
                if isinstance(map_approach, str):
                    field = {field_name: default_content.get(map_approach)}
                elif callable(map_approach):
                    try:
                        field = {field_name: map_approach(content)}
                    except Exception as e:
                        log.exception(e)
                        log.error('Error rendering content for "{}"'.format(
                            field_name
                        ))
                        field = {field_name: None}

            overwrites = [name for name in field.keys()
                          if name in result.keys()]
            if overwrites:
                log.warning('{} defined by {} overwrite previous fields in '
                            'search.'.format(overwrites, mapper))

            result.update(field)
        structured_results.append(result)
    return structured_results


def get_pagination(total_results, offset,
                   per_page=get_setting('SEARCH_RESULTS_PER_PAGE')):
    """
    Prepare pagination according to Globus Search. Since Globus Search handles
    returning paginated results, we calculate the offsets and send along which
    results and how many.

    Returns: dict containing 'current_page' and a list of pages
    Example:
        {
        'current_page': 3,
        'pages': [{'number': 1},
           {'number': 2},
           {'number': 3},
           {'number': 4},
           {'number': 5},
           {'number': 6},
           {'number': 7},
           {'number': 8},
           {'number': 9},
           {'number': 10}]}
    pages: contains info which is easy for the template engine to render.
    """

    if total_results > per_page * get_setting('SEARCH_MAX_PAGES'):
        page_count = get_setting('SEARCH_MAX_PAGES')
    else:
        page_count = math.ceil(total_results / per_page) or 1
    pagination = [{'number': p + 1} for p in range(page_count)]

    return {
        'current_page': offset // per_page + 1,
        'pages': pagination
    }


def get_filters(filters):
    """
    Only used for backwards compatibility. Please see get_search_filters
    instead.
    """
    log.warning('"get_filters" is deprecated and will be removed in v0.4, '
                'please use "get_search_filters" instead.')
    return [{
        'type': 'match_all',
        'field_name': name,
        'values': values
    } for name, values in filters.items()]


def serialize_gsearch_range(gsearch_range):
    """
    Takes a range from Globus Search, and returns a string which can be used
    in a URL.
    :param gsearch_range: A dict: {'from': (number or *), 'to': (number or *)}
    :return: The same range turned into a string.
    """
    return '{}{}{}'.format(gsearch_range['from'],
                           FILTER_RANGE_SEPARATOR,
                           gsearch_range['to'])


def get_date_format_type(date_str):
    match = filter_date_matcher.match(date_str)
    if not match:
        return None
    date_matches = match.groupdict()
    date_format_set = {dt for dt, value in date_matches.items()
                       if value is not None}
    date_format_types = [
        ('year', {'year'}),
        ('month', {'year', 'month'}),
        ('day', {'year', 'month', 'day'}),
        ('time', {'year', 'month', 'day', 'time'}),
    ]
    for name, dft_set in date_format_types:
        if dft_set == date_format_set:
            return name
    fmt = filter(lambda name, fmt_set:
                 name if date_format_set == fmt_set else None,
                 date_format_types)
    return list(fmt) or None


def parse_date_filter(serialized_date):
    dt_fmt_type = get_date_format_type(serialized_date)
    dt_fmt_str = DATETIME_PARTIAL_FORMATS.get(dt_fmt_type)
    if dt_fmt_str:
        return {
            'value': serialized_date,
            'type': dt_fmt_type,
            'datetime': datetime.datetime.strptime(serialized_date, dt_fmt_str)
        }
    raise exc.InvalidRangeFilter(code='FilterParseError',
                                 message='Unable to parse {}'
                                         ''.format(serialized_date))


def parse_range_filter_bounds(range_filter):
    """
    Low level utility to parse the lower or upper range of a given range filter
    The given range filter MUST not be None.
    :param range_filter: String representation of a range filter.
    :return: Returns the float or int value of the range filter, or * if the
    filter is a wildcard '*'
    """
    if range_filter == '*':
        return '*'
    try:
        if '.' in range_filter:
            return float(range_filter)
        return int(range_filter)
    except ValueError:
        pass
    return parse_date_filter(range_filter)['value']


def deserialize_gsearch_range(serialized_filter_range):
    """
    Returns the value of a query parameter for the range type filter.
    This accepts two different kinds of ranges: ...

    :param serialized_filter_range: The value of the range query param
    :return: A dict resembling a result from Globus Search. Example:
    {'from': 10, 'to': 100}
    """
    separator_count = serialized_filter_range.count(FILTER_RANGE_SEPARATOR)
    if separator_count != 1:
        raise exc.InvalidRangeFilter(
            message='Filter {} did not contain separator {}'
                    ''.format(serialized_filter_range, FILTER_RANGE_SEPARATOR)
        )
    low, high = serialized_filter_range.split(FILTER_RANGE_SEPARATOR)
    if not low or not high:
        raise exc.InvalidRangeFilter(
            message='Filter Missing Bounds',
            code='{}BoundMissing'.format('Lower' if not low else 'Higher'))
    return {
        'from': parse_range_filter_bounds(low),
        'to': parse_range_filter_bounds(high)
    }


def get_field_facet_filter_types(facet_definitions, default_terms=None):
    cleaned_facets = prepare_search_facets(facet_definitions)
    field_types = {}
    for facet in cleaned_facets:
        field = facet['field_name']
        if facet['type'] == 'terms':
            field_types[field] = (
                facet.get('filter_type') or
                default_terms or
                get_setting('DEFAULT_FILTER_MATCH')
            )
        elif facet['type'] == 'numeric_histogram':
            field_types[field] = FILTER_RANGE
        elif facet['type'] == 'date_histogram':
            field_types[field] = (facet.get('filter_type') or
                                  facet['date_interval'])
        else:
            raise ValueError('Unknown filter type: {}'.format(facet['type']))
    return field_types


def resolve_date_facet_value_from_range(date_range, date_interval):
    """
    Resolve a date range into a single string formatted date according to the
    date_interval.

    :param date_range:
    :param date_interval:
    :return:
    """
    dt_from = parse_date_filter(date_range['from'])['datetime']
    dt_to = parse_date_filter(date_range['to'])['datetime']
    dt_middle = dt_from + (dt_to - dt_from) / 2
    date_pattern = DATETIME_PARTIAL_FORMATS.get(date_interval)
    return dt_middle.strftime(date_pattern)


def get_facets(search_result, portal_defined_facets, filters,
               filters_types=None):
    """Prepare facets for display. Globus Search data is removed from results
    and the results are ordered according to the facet map. Empty categories
    are removed and any filters the user checked are tracked.

    :param search_result: A raw search result from Globus Search
    :param portal_defined_facets: 'facets' defined for a search index in
        settings.py
    :param filters: A list of user selected filters from get_search_filters()
    This is used to determine if the filter a user chose matches one of the
    portal's defined facets. Since a search has already happened by this point,
    `filters` only determines the look of the page (which box is checked) and
    generates the query-params for the user's next possible search.
    :param filter_match: Filtering behavior for next query. 'match-all', or
    'match-any'.

    :return: A list of facets. An example is here:
        [
            {
            'name': 'Contributor'
            'buckets': [{
                   'checked': False,
                   'count': 4,
                   'field_name': 'searchdata.contributors.contributor_name',
                   'value': 'Cobb, Jane'},
                  {'checked': True,
                   'count': 4,
                   'field_name': 'searchdata.contributors.contributor_name',
                   'value': 'Reynolds, Malcolm'}
                   # ...<More Buckets>
                   ],
            },
            # ...<More Facets>
        ]

      """
    filter_types = get_field_facet_filter_types(portal_defined_facets)
    active_filters = {filter['field_name']: filter for filter in filters}
    facets = search_result.data.get('facet_results', [])
    # Remove facets without buckets so we don't display empty fields
    pruned_facets = {f['name']: f['buckets'] for f in facets if f['buckets']}
    cleaned_facets = []
    for f in portal_defined_facets:
        buckets = pruned_facets.get(f['name'])
        if buckets:
            facet = {'name': f['name'], 'buckets': []}
            actv_filter = active_filters.get(f['field_name'], {})
            for bucket in buckets:
                filter_type = filter_types[f['field_name']]
                query_key = get_search_filter_query_key(f['field_name'],
                                                        filter_type)
                if filter_type == FILTER_RANGE:
                    bucket_vals = serialize_gsearch_range(bucket['value'])
                else:
                    bucket_vals = bucket['value']

                if filter_type in FILTER_DATE_RANGES:
                    active_date_vals = [
                        resolve_date_facet_value_from_range(v, filter_type)
                        for v in actv_filter.get('values', [])
                    ]
                    checked = bucket['value'] in active_date_vals
                else:
                    checked = bucket['value'] in actv_filter.get('values', [])
                facet['buckets'].append({
                    'count': bucket['count'],
                    'field_name': f['field_name'],
                    'filter_type': filter_type,
                    'search_filter_query_key': query_key,
                    'checked': checked,
                    'value': bucket_vals,
                })
            cleaned_facets.append(facet)
    return cleaned_facets
