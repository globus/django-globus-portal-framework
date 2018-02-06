from __future__ import division

import json
from six.moves.urllib.parse import quote_plus
import globus_sdk

from django.conf import settings


def load_json_file(filename):
    with open(filename) as f:
        raw_data = f.read()
        return json.loads(raw_data)


def default_search_mapper(entry):
    """This will become a simple function, to map data in a search result
    to fields in datacite, assuming everything maps cleanly. Other search
    indices will be expected to override this behavior for their custom
    schemas.
    """
    return mdf_to_datacite(entry)


def process_search_data(search_result, index):
    """
    Process results in a general search result, running the mapping function
    for each result and preparing other general data for being shown in
    templates (such as quoting the subject and including the index).
    :param search_result:
    :param index:
    :return:
    """
    results = []
    for entry in search_result.data['gmeta']:
        result = {
            'index': index,
            'subject': quote_plus(entry['subject'])
        }
        result.update(default_search_mapper(entry['content'])),
        results.append(result)
    return results


def _get_pagination(search_result, per_page=settings.SEARCH_RESULTS_PER_PAGE):
    """
    Prepare pagination according to Globus Search. Since Globus Search handles
    returning paginated results, we calculate the offsets and send along which
    results and how many.
    """

    if search_result.data['total'] > per_page * settings.SEARCH_MAX_PAGES:
        page_count = settings.SEARCH_MAX_PAGES
    else:
        page_count = search_result.data['total'] // per_page or 1
    pagination = [{'number': p + 1} for p in range(page_count)]

    return {
        'current_page': search_result.data['offset'] // per_page + 1,
        'pages': pagination
    }


def _get_filters(filters):
    """
    Get Globus Search filters for each facet. Currently only supports
    "match_all".
    :param filters:
    :return:
    """
    return [{
        'type': 'match_all',
        'field_name': name,
        'values': values
    } for name, values in filters.items()]


def _get_facets(search_result, facet_map, filters):
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


def search(index, query, filters, user=None, page=1):
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
    facet_map = load_json_file(settings.SEARCH_SCHEMA)
    gfilters = _get_filters(filters)
    result = client.post_search(
        index,
        {
            'q': query,
            'facets': facet_map['facets'],
            'filters': gfilters,
            'offset': (int(page) - 1) * settings.SEARCH_RESULTS_PER_PAGE,
            'limit': settings.SEARCH_RESULTS_PER_PAGE
        })
    return {'search_results': process_search_data(result, index),
            'facets': _get_facets(result, facet_map, filters),
            'result': result,
            'pagination': _get_pagination(result)}


def load_search_client(user):
    if user.is_authenticated:
        token = user.social_auth.get(provider='globus')\
            .extra_data['access_token']
        authorizer = globus_sdk.AccessTokenAuthorizer(token)
        return globus_sdk.SearchClient(authorizer=authorizer)
    return globus_sdk.SearchClient()


def mdf_to_datacite(data):
    """TEST DATA!!! This is used as a stand-in for a Globus Search index
    which has not been setup yet. Once we switch over to the new index,
    this function should be deleted."""
    # General datacite 4.1
    datacite = {
            "alternate_identifiers": data[0]['mdf'].get('scroll_id', ''),
            "contributors": "",
            "creators": "Materials Data Facility",
            "dates": data[0]['mdf']['ingest_date'],
            "descriptions": "",
            "formats": data[0]['mdf'].get('tags'),
            "funding_references": "",
            "geo_locations": "",
            "identifier": data[0]['mdf']['mdf_id'],
            "language": "",
            "publication_year": "",
            "publisher": "",
            "related_identifiers": "",
            "resource_type": "application/json",
            "rights_list": "",
            "sizes": "",
            "subjects": list(data[0].get('dss_tox', {}).values()),
            "titles": data[0]['mdf']['title'],
            "version": data[0]['mdf']['metadata_version']
    }
    return datacite
