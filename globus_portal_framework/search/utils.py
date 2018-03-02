from __future__ import division

import json
import logging
from importlib import import_module
from urllib.parse import quote_plus, unquote
import globus_sdk

from globus_portal_framework.search import settings
from globus_portal_framework.utils import load_globus_client

log = logging.getLogger(__name__)


def load_json_file(filename):
    with open(filename) as f:
        raw_data = f.read()
        return json.loads(raw_data)


SEARCH_SCHEMA = load_json_file(settings.SEARCH_SCHEMA)


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
    gfilters = get_filters(filters)
    result = client.post_search(
        index,
        {
            'q': query,
            'facets': SEARCH_SCHEMA['facets'],
            'filters': gfilters,
            'offset': (int(page) - 1) * settings.SEARCH_RESULTS_PER_PAGE,
            'limit': settings.SEARCH_RESULTS_PER_PAGE
        })
    return {'search_results': process_search_data(result.data['gmeta']),
            'facets': get_facets(result, SEARCH_SCHEMA, filters),
            'pagination': get_pagination(result.data['total'],
                                         result.data['offset'])
            }


def default_search_mapper(gmeta_result, schema):
    """This mapper takes the given schema and maps all fields within the
    gmeta entry against it. Any non-matching results simply won't
    show up in the result. This approach avoids a bunch of empty fields being
    displayed when rendered in the templates.
    :param entry:
        entry = {
            'foo': 'bar'
            'car': 'zar'
        }
    :param schema:
        schema = {
            'foo': {'field_title': 'Foo'}
        }
    :returns template_results:
    Will return:
        {
        'foo': {'field_title': 'Foo', 'value': 'bar'}
        }
    """
    entry = gmeta_result[0][settings.SEARCH_ENTRY_FIELD_PATH]
    fields = {k: {
                       'field_title': schema[k].get('field_title', k),
                       'data': v
                  } for k, v in entry.items() if schema.get(k)}
    if not fields.get('title'):
        fields['title'] = entry.get(settings.SEARCH_ENTRY_TITLE)
        if isinstance(fields['title'], list):
            fields['title'] = fields['title'].pop(0)
    return fields


def get_subject(subject, user):
    """Get a subject and run the result through the SEARCH_MAPPER defined
    in settings.py. If no subject exists, return context with the 'subject'
    and an 'error' message."""
    client = load_search_client(user)
    try:
        result = client.get_subject(settings.SEARCH_INDEX, unquote(subject))
        return process_search_data([result.data])[0]
    except globus_sdk.exc.SearchAPIError:
        return {'subject': subject, 'error': 'No data was found for subject'}


def load_search_client(user):
    """Load a globus_sdk.SearchClient, with a token authorizer if the user is
    logged in or a generic one otherwise."""
    return load_globus_client(user, globus_sdk.SearchClient,
                              'search.api.globus.org')


def process_search_data(results):
    """
    Process results in a general search result, running the mapping function
    for each result and preparing other general data for being shown in
    templates (such as quoting the subject and including the index).
    :param results: List of GMeta results, which would be the r.data['gmeta']
    in from a simple query to Globus Search. See here:
    https://docs.globus.org/api/search/schemas/GMetaResult/
    :return: A list of search results:


    """
    mod_name, func_name = settings.SEARCH_MAPPER
    mod = import_module(mod_name)
    mapper = getattr(mod, func_name, default_search_mapper)
    structured_results = []
    for entry in results:
        structured_results.append({
            'subject': quote_plus(entry['subject']),
            'fields': mapper(entry['content'], SEARCH_SCHEMA['fields'])
        })
    return structured_results


def get_pagination(total_results, offset,
                   per_page=settings.SEARCH_RESULTS_PER_PAGE):
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

    if total_results > per_page * settings.SEARCH_MAX_PAGES:
        page_count = settings.SEARCH_MAX_PAGES
    else:
        page_count = total_results // per_page or 1
    pagination = [{'number': p + 1} for p in range(page_count)]

    return {
        'current_page': offset // per_page + 1,
        'pages': pagination
    }


def get_filters(filters):
    """
    Get Globus Search filters for each facet. Currently only supports
    "match_all".

    :param filters: A dict where the keys are filters and the values are a
    list of elements to filter on.
    :return: a list of formatted filters ready to send off to Globus Search

    Example:
        {'elements': ['O', 'H'], 'publication_year': ['2017', '2018']}
    Returns:
        List of GFilters, suitable for Globus Search:
        https://docs.globus.org/api/search/schemas/GFilter/

    """
    return [{
        'type': 'match_all',
        'field_name': name,
        'values': values
    } for name, values in filters.items()]


def get_facets(search_result, facet_map, filters):
    """Go through a search result, and add an attribute 'checked' to all facets
    which were originally provided as filters in the result. """
    facets = search_result.data.get('facet_results', [])
    # Create a table we can use to lookup facets by name
    fac_lookup = {f['name']: f['field_name'] for f in facet_map['facets']}
    # Set the field_name identifier on each facet
    for facet in facets:
        for bucket in facet['buckets']:
            bucket['field_name'] = fac_lookup[facet['name']]
            filtered_facets = filters.get(bucket['field_name'])
            if filtered_facets and bucket['value'] in filtered_facets:
                bucket['checked'] = True
    return facets
