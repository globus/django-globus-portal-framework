from __future__ import division
import os
import re
import json
import logging
import math
import collections
import datetime
import pathlib
from packaging import version
from urllib.parse import quote_plus, unquote
import globus_sdk
from django import template
from django.utils.module_loading import import_string
from django.conf import settings

from globus_portal_framework.apps import get_setting
from globus_portal_framework import load_search_client, IndexNotFound, exc
from globus_portal_framework.constants import (
    FILTER_QUERY_PATTERN, FILTER_TYPES, FILTER_RANGE,
    FILTER_DATE_RANGES, FILTER_DEFAULT_RANGE_SEPARATOR,
    FILTER_DATE_TYPE_PATTERN, DATETIME_PARTIAL_FORMATS,
    FACET_NAME_PATTERN,

    FILTER_YEAR, FILTER_MONTH, FILTER_DAY, FILTER_HOUR, FILTER_MINUTE,
    FILTER_SECOND,

    VALID_SEARCH_FACET_KEYS, VALID_SEARCH_KEYS,

    DEFAULT_FACET_MODIFIERS,
)
FILTER_RANGE_SEPARATOR = getattr(settings, 'FILTER_RANGE_SEPARATOR',
                                 FILTER_DEFAULT_RANGE_SEPARATOR)


log = logging.getLogger(__name__)
filter_query_matcher = re.compile(FILTER_QUERY_PATTERN)
filter_date_matcher = re.compile(FILTER_DATE_TYPE_PATTERN)
facet_name_matcher = re.compile(FACET_NAME_PATTERN)


def post_search(index, query, filters, user=None, page=1, search_kwargs=None):
    """Perform a search and return the relevant data for display to the user.
    The search results are processed through fields defined in the index
    data 'fields' in SEARCH_RESULTS. Facets are processed to determine which
    sidebar facets should appear 'checked' based on the filters passed in.
    Pagination is processed to determine which page should be highlighted at
    the bottom of the page. Other items, such as count, offset, and total, are
    all returned verbatim from Globus Search.
    {
        'search_results': [{'title': 'My title'...} ...],
        'facets: [{'buckets': [{'checked': False,
                          'count': 35,
                          'field_name': 'foo',
                          'filter_type': 'match-all',
                          'search_filter_query_key': 'filter-match-all.foo',
                          'value': 'myval'}],
                    'name': 'Subject'},]',
        'pagination: {'current_page': 1,
                      'pages': [{'number': 1},
                                {'number': 2},
                                {'number': 3},
                                {'number': 4}]},',
        'count: 10',
        'offset': 0,
        'total: 35'
    }

    See Search docs here:
    https://docs.globus.org/api/search/reference/get_query/
    :param index: index key name defined in settings.SEARCH_INDEXES, eg 'foo'
    :param query: The query string to search with, eg 'apples' or '*'
    :param filters: List of search filters. Typically, this is taken from the
        request: in globus_portal_framework.gsearch.get_search_filters()
    :param user: The user associated with the request (request.user) or None
    :param page: The page number to search on. This is calculated with
        settings.SEARCH_RESULTS_PER_PAGE, and sent along to Globus Search
    :param search_kwargs: Custom overrides to send along to Globus Search. This
        can be used to replace existing args, such as 'facets', or specify
        new or experimental args supported by Globus Search but not DGPF.
    """
    if not index or not query:
        return {'search_results': [], 'facets': []}

    client = load_search_client(user)
    index_data = get_index(index)
    search_data = {k: index_data[k] for k in VALID_SEARCH_KEYS
                   if k in index_data}
    search_data.update({
        'q': query,
        'facets': prepare_search_facets(index_data.get('facets', [])),
        'filters': filters,
        'offset': (int(page) - 1) * get_setting('SEARCH_RESULTS_PER_PAGE'),
        'limit': get_setting('SEARCH_RESULTS_PER_PAGE')
    })
    search_data.update(search_kwargs or {})
    try:
        result = client.post_search(index_data['uuid'], search_data)
        return {
            'search_results': process_search_data(index_data.get('fields', []),
                                                  result.data['gmeta']),
            'facets': get_facets(result, index_data.get('facets', []),
                                 filters, index_data.get('filter_match'),
                                 index_data.get('facet_modifiers', [])),
            'pagination': get_pagination(result.data['total'],
                                         result.data['offset']),
            'count': result.data['count'],
            'offset': result.data['offset'],
            'total': result.data['total'],
            }
    except globus_sdk.SearchAPIError as sapie:
        log.exception(sapie)
        etext = ('There was an error in {}, you can file '
                 'an issue here:\n{}\nWith the following data: \n\n')
        gs = 'https://github.com/globusonline/globus-search/issues'
        dgpf = 'https://github.com/globus/django-globus-portal-framework'
        if str(sapie.http_status).startswith('5'):
            error = etext.format('Globus Search', gs)
        else:
            error = etext.format('Globus Portal Framework', dgpf)
        full_error = '{}Index ID: {}\nAuthenticated? {}\nParams: \n{}'.format(
            error, index_data['uuid'],
            user.is_authenticated if user else False,
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
        filter_match_default=get_setting('DEFAULT_FILTER_MATCH')
        ):
    """Given a request, fetch all query params for filters and return a list
    that can be sent to Globus Search. Filter types are
    parsed from the following keys:
        * filter.<field_name>
        * filter-match-all.<field_name>
        * filter-match-any.<field_name>
        * filter-range.<field_name>
        * filter-year.<field_name>
        * filter-month.<field_name>
        * filter-day.<field_name>
        * filter-hour.<field_name>
        * filter-minute.<field_name>
        * filter-second.<field_name>

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
    return filters


def get_date_range_for_date(date_str, interval):
    """
    Given a date string, parse it and derive a range based on the given
    interval. The interval is inclusive on the lower end, and exclusve on the
    higher end. For example, given a date str of 2019-03-10 and a 'month'
    interval, this will return a range of 2019-03-01 -- 2019-03-31.
    :param date_str: Any ISO date or partial date. 2019, 2019-03,
    2019-03-01, 2019-12-18 21:00:00
    :param interval: Any interval defined in
    globus_portal_framework.constants.FILTER_DATE_RANGES. Examples include:
    'year', 'month', 'day', 'hour'
    :return:
    A date range dict. Example:
    {
      'from': '2019-12-18 21:00:00'
      'to': '2019-12-18 21:00:01'
    }
    """
    dt = parse_date_filter(date_str)['datetime']
    # If filtering on a month or year, chop off the extra part of the
    # datetime so we don't accidentally search on the previous month
    # or next month
    day = datetime.timedelta(days=1)
    if interval == FILTER_SECOND:
        second = datetime.timedelta(seconds=1)
        from_d, to_d = dt - second, dt + second
    elif interval == FILTER_MINUTE:
        from_d = dt.replace(second=0)
        to_d = from_d + datetime.timedelta(seconds=59)
    elif interval == FILTER_HOUR:
        from_d = dt.replace(minute=0, second=0)
        to_d = from_d + datetime.timedelta(minutes=59, seconds=59)
    elif interval == FILTER_DAY:
        dt = dt.replace(hour=0, minute=0, second=0)
        from_d, to_d = dt, dt + day
    elif interval == FILTER_MONTH:
        from_d = dt.replace(day=1, hour=0, minute=0, second=0)
        inc_month = 1 if dt.month == 12 else dt.month + 1
        inc_year = dt.year + 1 if inc_month == 1 else dt.year
        to_d = from_d.replace(month=inc_month, year=inc_year) - day
    elif interval == FILTER_YEAR:
        dt = dt.replace(day=1, month=1, hour=0, minute=0, second=0)
        year = datetime.timedelta(days=365)
        from_d, to_d = dt, dt + year
    else:
        raise exc.GlobusPortalException('Invalid date type {}'
                                        ''.format(interval))
    # Globus search can handle any time format, so using the most precise will
    # work every time.
    dt_format_type = DATETIME_PARTIAL_FORMATS['time']
    return {
        'from': from_d.strftime(dt_format_type),
        'to': to_d.strftime(dt_format_type)
    }


def parse_filters(filter_values, filter_type):
    """
    Parse raw filters and return a list of parsed filter values. If the type
    is a match type filter (MATCH_ANY or MATCH_ALL), no processing is done and
    the list is simply returned. If the filter type is of type 'range', the
    returned value will be a list of dicts with each dict containing 'from' and
    'to' keys. 'range' type filters may be either date strings, ints or floats.
    For filter types of a date interval ('year', 'month', 'day', 'hour',
    'minute', 'second'), the date is parsed and a range is derived according to
    the date interval passed in. The date filter given may be more exact than
    the interval, but if the interval doesn't contain enough info for the
    filter given (for example, searching on the 'month' for 2020), the value is
    assumed to be the minimum incremental interval (for example, January 2020)
    :param filter_values: A list of raw filter values. List values can be
    strings, date strings, number ranges, or date ranges.
    Valid examples:
      ['application/x-hdf', 'image/png']
      ['2019-10-25 16:43:00', '2019-10-25 16:43:00']
      ['2019-10-25 16:43:00--2019-10-25 16:43:00']
      ['1--100']
    :param filter_type:
      Filter type to match the corresponding filter values. Can be any value
      in globus_portal_framework.constants.FILTER_TYPES, but must match the
      type given.
    Valid examples: FILTER_TYPES.RANGE, FILTER_TYPES.YEAR
    :return: A list. If filter type is match-all or match-any, the list items
    will be strings. If the filter type is a range or date interval, the list
    items will be dicts with 'from' and 'to' keys.
    """
    if filter_type in FILTER_DATE_RANGES:
        return [get_date_range_for_date(date_str, filter_type)
                for date_str in filter_values]
    elif filter_type == FILTER_RANGE:
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
    else:
        return list(filter_values)


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


def generate_globus_search_facet_name(facet_definition, order_index):
    """
    Generate a unique field name for GS. This is needed to ensure we can
    match the portal-defined facet since type and field_name info is not
    present on facets returned from Globus Search.
    Only idx is used to determine the correct facet, other info is for
    human readability in case of an error
    """
    return 'facet_def_{}_{}'.format(order_index,
                                    facet_definition['field_name'])


def resolve_facet_results(portal_defined_facets, facet_results):
    """
    Resolve and combine the results from Globus Search to the portal defined
    facets. Resolution is done via parsing the ID generated by
    generate_globus_search_facet_name(). ID generation is currently internal
    and cannot be changed, this function is tightly coupled to the function
    above.

    Returns a list of portal defined facets with additional results from Globus
    search added: unique_name, buckets, and value. The ordering exactly matches
    the ordering of facets defined in settings.py
    """
    # Set general facet information. prepare_search_facets will ensure we get
    # all GS fields and the dev didn't leave anything out in the definition.
    facets = prepare_search_facets(portal_defined_facets)
    for prepped_facet, def_facet in zip(facets, portal_defined_facets):
        prepped_facet['unique_name'] = prepped_facet.pop('name')
        prepped_facet['name'] = def_facet.get('name', def_facet['field_name'])

    # Set all of the facet results that came back from Globus Search on the
    # facets defined above.
    for fresult in facet_results:
        match = facet_name_matcher.match(fresult['name'])
        if not match:
            # Gather detailed error for the facet that doesn't match.
            # Skip this facet so we're not forcing a hard stop 500 for
            # the user. Working facets will still be rendered. This should
            # Probably never happen unless we want to support custom facet id
            # generation, a feature probably nobody would be interested in.
            pfacets = prepare_search_facets(portal_defined_facets)
            names = ', '.join([pf['name'] for pf in pfacets])
            log.error('Facet "{}" from Globus Search did not match any '
                      'configured facets: {}'.format(fresult['name'], names))
            continue
        name = match.groupdict()
        idx = int(name['order_index'])
        if fresult.get('buckets') is not None:
            facets[idx]['buckets'] = fresult['buckets']
        else:
            facets[idx]['value'] = fresult['value']
    return facets


def prepare_search_facets(facets):
    """Prepare a list of facets to be sent to Globus Search. Globus Portal
    Framework defines some settings in the 'facets' section which are not
    valid search fields. This both strips invalid fields, and adds sensible
    defaults if required info is missing."""
    cleaned_facets = []
    for idx, facet in enumerate(facets):
        if not isinstance(facet, dict):
            raise ValueError('Each facet must be of type "dict"')
        cfacet = {k: v for k, v in facet.items()
                  if k in VALID_SEARCH_FACET_KEYS}
        if not cfacet.get('field_name'):
            raise ValueError('Each facet must define at minimum "field_name"')
        cfacet['name'] = generate_globus_search_facet_name(facet, idx)
        cfacet['type'] = cfacet.get('type', 'terms')
        if cfacet['type'] not in ['date_histogram', 'sum', 'avg']:
            cfacet['size'] = cfacet.get('size', 10)
        cleaned_facets.append(cfacet)
    return cleaned_facets


def get_template_path(template, index=None):
    """Get the base template path to a given template
    set and return the setting prefix with the ``template`` given.
    The template set can either be a setting per-index with the
    ``base_templates`` setting, or global as ``BASE_TEMPLATES``
    in settings.py.

    This is primarily used to allow operation between newer Globus Portal
    Framework templates (globus_portal_framework/v2) and older versions
    of templates. This would also allow users to draft an entirely new set
    of base templates, if they wished.

    :param template: Path to template. Ex: search.html
    :param index: The name of the index (key in SEARCH_INDEXES). Optional.


    """
    index_data = get_index(index) if index is not None else {}
    prefix = (
            index_data.get('base_templates') or
            get_setting('BASE_TEMPLATES') or
            ''
    )
    return str(pathlib.Path(prefix) / template)


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
    except globus_sdk.SearchAPIError:
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
    for gmeta_result in results:

        entries = gmeta_result['entries']
        content = [e['content'] for e in entries]
        result = {
            'subject': quote_plus(gmeta_result['subject']),
            'all': content
        }

        if len(content) == 0:
            log.warning('Subject {} contained no content, skipping...'.format(
                gmeta_result['subject']
            ))
            continue
        default_content = content[0]

        for mapper in field_mappers:
            field = {}
            if isinstance(mapper, str):
                field = {mapper: default_content.get(mapper)}
            elif isinstance(mapper, collections.abc.Iterable) \
                    and len(mapper) == 2:
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
    """
    Given a date_str, derive the date information contained within the date_str
    The return value is based on the following map:
    'year': 'YYYY'
    'month': 'YYYY-MM'
    'day': 'YYYY-MM-DD'
    'time': 'YYYY-MM-DD hh:mm:ss'
    and will return 'year', 'month', 'day' or 'time'

    Examples:
        '2019' will return 'day'
        '2018-01-20 12:30:34' will return 'time'
    If you want a parsed datetime object, see 'parse_date_filter()' instead.
    """
    date_str = str(date_str)
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


def parse_date_filter(serialized_date):
    """
    Given a serialized_date (ex: '2019-12-02'), return a dict containing
    the following info:
    {
      'value': serialized_date,
      'type': 'day',
      'datetime': <datetime.datetime object>
    }
    The date string given can match any date string format types handled by
    get_date_format_type()
    :param serialized_date: a date string, ex: '2019-12-02'
    :return: A dict containing the date string given, whether the date is a
    year, month, day or time type date, and a datetime object.
    """
    # coerce date into str, in case the date was pased as a number, eg 2020
    sdate = str(serialized_date)
    dt_fmt_type = get_date_format_type(sdate)
    dt_fmt_str = DATETIME_PARTIAL_FORMATS.get(dt_fmt_type)
    if dt_fmt_str:
        return {
            'value': serialized_date,
            'type': dt_fmt_type,
            'datetime': datetime.datetime.strptime(sdate, dt_fmt_str)
        }
    raise exc.InvalidRangeFilter(code='FilterParseError',
                                 message='Unable to parse {}'
                                         ''.format(sdate))


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


def get_facet_filter_type(facet_definition, default_terms=None):
    """Given a definition from settings.SEARCH_INDEXES.facets,
    derive the corresponding filter which should be used for
    filtering on the data returned in Globus Search facets.

    Returns a valid Globus Search filter type, or None if the given facets
    cannot be filtered on. A warning will be raised if the facet definition
    does not match any known types in Globus Search -- in this case, filtering
    on the unknown type will not be possible but no errors will be raised.
    """
    ftype = facet_definition.get('type', 'terms')
    field = facet_definition['field_name']
    if ftype == 'terms':
        return (
                facet_definition.get('filter_type') or
                default_terms or
                get_setting('DEFAULT_FILTER_MATCH')
        )
    elif ftype == 'numeric_histogram':
        return FILTER_RANGE
    elif ftype == 'date_histogram':
        return (facet_definition.get('filter_type') or
                facet_definition['date_interval'])
    elif ftype in ['sum', 'avg']:
        return None
    else:
        log.warning('Filter type could not be determined for facet "{}" '
                    'facet type "{}" is not know by DGPF. Filtering will '
                    'be disabled for this field.'.format(field, ftype))
    return None


def get_field_facet_filter_types(facet_definitions, default_terms=None):
    """Deprecated and no longer used. Will be removed in v0.4.0"""
    field_types = {}
    for facet in facet_definitions:
        ftype = facet.get('type', 'terms')
        field = facet['field_name']
        if ftype == 'terms':
            field_types[field] = (
                facet.get('filter_type') or
                default_terms or
                get_setting('DEFAULT_FILTER_MATCH')
            )
        elif ftype == 'numeric_histogram':
            field_types[field] = FILTER_RANGE
        elif ftype == 'date_histogram':
            field_types[field] = (facet.get('filter_type') or
                                  facet['date_interval'])
        elif ftype in ['sum', 'avg']:
            field_types[field] = None
        else:
            raise ValueError('Unknown filter type: {}'.format(ftype))
    return field_types


def get_active_filters(facet_field_name, filter_type, user_filters):
    """
    Given a list of all user search filter query params, derive a list
    of active filters which can be matched up against facets. The return
    value will be a list of filters for a given facet field and type which
    can be checked against facet buckets to determine which bucket a user
    wants to use to filter their search.

    The return values are tailored to be as easy as possible to compare against
    existing facets. For Terms, and Numeric Histograms, it's easiest to compare
    against the raw value and serialized value respectively. Date filters are
    different, where the user specifies a range of time around a certain date,
    such as a "Month" filter of February being Feb 1st 2018 to Feb 28th 2018.
    Datetimes MUST be used to compare facets due to the specificity of facets.
    A filter might look like "2018-02" but Globus Search fields can have
    different formats such as "2018-02-16" or "2018-02-16 00:00:00" which
    cannot be matched by string.

    Example return values below:
    Match-Any, Match-All filter Example: ['sheep', 'rainbow', 'lollipop']
    Numeric Range Filter Example: ['18000.0--19500.0']
    Date Range Filter Example: [{
      'from': datetime.datetime(2018, 2, 1, 0, 0),
      'to': datetime.datetime(2018, 2, 28, 0, 0)
    }]
    """
    gs_filter_type = FILTER_TYPES[filter_type]
    filter_vals_nested = [uf.get('values', []) for uf in user_filters
                          if (uf['field_name'] == facet_field_name and
                          uf['type'] == gs_filter_type)]
    # Flatten the filter values into a simple list
    filter_vals = [item for sublist in filter_vals_nested for item in sublist]

    if filter_type in FILTER_DATE_RANGES:
        filter_vals = [{
            'from': parse_date_filter(f['from'])['datetime'],
            'to': parse_date_filter(f['to'])['datetime']
        } for f in filter_vals]
    elif filter_type == FILTER_RANGE:
        filter_vals = [serialize_gsearch_range(r) for r in filter_vals]
    return filter_vals


def get_facets(search_result, portal_defined_facets, filters,
               filter_match=None, facet_modifiers=None):
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
    :param filter_match: Deprecated. Please set filtering behavior in the
    facet definition.
    :param facet_modifiers: A list of shim function import strings which
    modify the output of facets before search data is returned to the
    Django view. This provides a handy way to provide index-level edits to
    facet data while leaving views unchanged. Each import string should take
    a single parameter for the list of facets. Each function is called in the
    order it is defined.

    :return: A list of facets. An example is here:
        [
            {
            'name': 'Contributor'
            'field_name': 'myfields.contributors.value',
            'size': 10,
            'type': 'terms',
            'unique_name': 'facet_def_0_myfields.contributors.value'
            'buckets': [{
                   'checked': False,
                   'count': 4,
                   'datetime': None,
                   'field_name':
                       'searchdata.contributors.contributor_name,
                   'filter_type': 'match-all',
                   'search_filter_query_key':
                       'filter-match-all.searchdata.contributors.contributor_name',  # noqa
                   'value': 'Cobb, Jane'},
                  {'checked': True,
                   'count': 4,
                   'datetime': None,
                   'field_name': 'searchdata.contributors.contributor_name',
                   'filter_type': 'match-all',
                   'search_filter_query_key':
                       'filter-match-all.myfields.contributors.value',
                   'value': 'Reynolds, Malcolm'}
                   # ...<More Buckets>
                   ],
            },
            # ...<More Facets>
        ]

    """
    facets = resolve_facet_results(portal_defined_facets,
                                   search_result.data.get('facet_results', []))
    for facet in facets:
        # Some facet types, like avg and sum, don't have buckets. Skip them
        # completely.
        buckets = facet.get('buckets')
        if not buckets:
            continue

        # Get the filter type, and any active filters for this category.
        # active_filters will determine which buckets are 'checked'
        filter_type = get_facet_filter_type(facet, default_terms=filter_match)
        active_filter_vals = get_active_filters(facet['field_name'],
                                                filter_type, filters)
        for bucket in buckets:
            # Remove any extra Globus Search keys, only keep data relevant
            # to the search.
            for extraneous_key in set(bucket).difference({'count', 'value'}):
                bucket.pop(extraneous_key)

            # Add filtering info to the bucket, and any extra general context
            bucket.update({
                'search_filter_query_key': get_search_filter_query_key(
                    facet['field_name'], filter_type),
                'field_name': facet['field_name'],
                'filter_type': filter_type,
            })

            # If the bucket value is a range, serialize it
            if filter_type == FILTER_RANGE:
                bucket['value'] = serialize_gsearch_range(bucket['value'])

            # Set "Checked" Value, and datetime if applicable
            if filter_type in FILTER_DATE_RANGES:
                buck_dt = parse_date_filter(bucket['value'])['datetime']
                bucket['checked'] = any([
                    buck_dt >= afilter['from'] and buck_dt < afilter['to']
                    for afilter in active_filter_vals
                ])
                bucket['datetime'] = buck_dt
            else:
                bucket['checked'] = bucket['value'] in active_filter_vals
                bucket['datetime'] = None
    # Apply user modifications to all finished facets. Catch ALL facet mod
    # exceptions. Typically, this happens due to an edge case in the modifier,
    # and should not result in the search page failing to load.
    facet_modifiers = (facet_modifiers if facet_modifiers is not None
                       else DEFAULT_FACET_MODIFIERS)
    for fmodder in facet_modifiers:
        try:
            facets = import_string(fmodder)(facets)
        except ImportError:
            # Don't catch these. Developer error.
            raise
        except Exception as e:
            log.exception(e)
            log.error('Facet modifier raised exception {}'.format(fmodder))
    return facets
