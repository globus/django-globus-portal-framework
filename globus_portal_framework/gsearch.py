from __future__ import division
import os
import logging
import collections
from urllib.parse import quote_plus, unquote
import globus_sdk
from django import template
from django.conf import settings

from globus_portal_framework.apps import get_setting
from globus_portal_framework import load_search_client, IndexNotFound


log = logging.getLogger(__name__)


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
    index_data = get_index(index)
    result = client.post_search(
        index_data['uuid'],
        {
            'q': query,
            'facets': index_data['facets'],
            'filters': gfilters,
            'offset': (int(page) - 1) * get_setting('SEARCH_RESULTS_PER_PAGE'),
            'limit': get_setting('SEARCH_RESULTS_PER_PAGE')
        })
    return {'search_results': process_search_data(index_data['fields'],
                                                  result.data['gmeta']),
            'facets': get_facets(result, index_data['facets'], filters),
            'pagination': get_pagination(result.data['total'],
                                         result.data['offset'])
            }


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
    data = settings.SEARCH_INDEXES.get(index, None)
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
                    field = {field_name: map_approach(content)}

            if not field:
                log.error('Unable to process mapper "{}"'.format(mapper))
                continue

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


def get_facets(search_result, portal_defined_facets, filters):
    """Prepare facets for display. Globus Search data is removed from results
    and the results are ordered according to the facet map. Empty categories
    are removed and any filters the user checked are tracked.

    :param search_result: A raw search result from Globus Search
    :param portal_defined_facets: 'facets' defined for a search index in
        settings.py
    :param filters: A dict of user-selected filters, an example like this:
        {'searchdata.contributors.value': ['Cobb, Jane', 'Reynolds, Malcolm']}

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
    facets = search_result.data.get('facet_results', [])
    # Remove facets without buckets so we don't display empty fields
    pruned_facets = {f['name']: f['buckets'] for f in facets if f['buckets']}
    cleaned_facets = []
    for f in portal_defined_facets:
        buckets = pruned_facets.get(f['name'])
        if buckets:
            facet = {'name': f['name'], 'buckets': []}
            for bucket in buckets:
                facet['buckets'].append({
                    'count': bucket['count'],
                    'value': bucket['value'],
                    'field_name': f['field_name'],
                    'checked': bucket['value'] in filters.get(f['field_name'],
                                                              [])
                })
            cleaned_facets.append(facet)
    return cleaned_facets
