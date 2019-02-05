from __future__ import division
import os
import re
import json
import logging
import collections
from urllib.parse import quote_plus, unquote
import globus_sdk
from django import template

from globus_portal_framework.apps import get_setting
from globus_portal_framework import load_search_client, IndexNotFound
from globus_portal_framework.constants import (
    FILTER_QUERY_PATTERN, FILTER_TYPES, FILTER_RANGE
)


log = logging.getLogger(__name__)
filter_query_matcher = re.compile(FILTER_QUERY_PATTERN)


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
                                         result.data['offset'])
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


def get_search_filters(request,
                       filter_match_default=get_setting('DEFAULT_FILTER_MATCH')
                       ):
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
            filter = {
                'field_name': filter_name,
                'type': (FILTER_TYPES.get(filter_type, ) or
                         FILTER_TYPES[filter_match_default]),
                'values': request.GET.getlist(key)
            }

            if filter_type == FILTER_RANGE:
                filter['values'] = [deserialize_gsearch_range(v) for v in
                                    filter['values']]
            filters.append(filter)
    return filters


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
        page_count = total_results // per_page or 1
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
    return '{}--{}'.format(gsearch_range['from'], gsearch_range['to'])


def deserialize_gsearch_range(serialized_filter_range):
    """
    Returns the value of a query parameter for the range type filter.
    :param serialized_filter_range: The value of the range query param
    :return: A dict resembling a result from Globus Search. Example:
    {'from': 10, 'to': 100}
    """
    grange = {}
    low, high = serialized_filter_range.split('--')
    if low == '*':
        grange['from'] = '*'
    else:
        grange['from'] = float(low) if '.' in low else int(low)

    if high == '*':
        grange['to'] = '*'
    else:
        grange['to'] = float(high) if '.' in high else int(high)
    return grange


def get_facets(search_result, portal_defined_facets, filters,
               filter_match=None):
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
    filter_map = {filter['field_name']: filter for filter in filters}
    facets = search_result.data.get('facet_results', [])
    # Remove facets without buckets so we don't display empty fields
    pruned_facets = {f['name']: f['buckets'] for f in facets if f['buckets']}
    cleaned_facets = []
    for f in portal_defined_facets:
        buckets = pruned_facets.get(f['name'])
        if buckets:
            facet = {'name': f['name'], 'buckets': []}
            filter = filter_map.get(f['field_name'], {})
            for bucket in buckets:
                buck = {
                    'count': bucket['count'],
                    'field_name': f['field_name'],
                    'checked': bucket['value'] in filter.get('values', []),
                }
                if isinstance(bucket['value'], dict):
                    buck['filter_type'] = FILTER_RANGE
                    buck['value'] = serialize_gsearch_range(bucket['value'])
                    qk = get_search_filter_query_key(f['field_name'],
                                                     FILTER_RANGE)
                    buck['search_filter_query_key'] = qk
                else:
                    buck['value'] = bucket['value']
                    fm = filter_match or get_setting('DEFAULT_FILTER_MATCH')
                    buck['filter_type'] = fm
                    qk = get_search_filter_query_key(f['field_name'], fm)
                    buck['search_filter_query_key'] = qk
                facet['buckets'].append(buck)
            cleaned_facets.append(facet)
    return cleaned_facets
