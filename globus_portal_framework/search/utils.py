from __future__ import division

import json
from six.moves.urllib.parse import quote_plus
import globus_sdk

from django.conf import settings


def load_json_file(filename):
    with open(filename) as f:
        raw_data = f.read()
        return json.loads(raw_data)


def _get_pagination(search_result, per_page=settings.SEARCH_RESULTS_PER_PAGE):

    if search_result.data['total'] > per_page * settings.SEARCH_MAX_PAGES:
        page_count = settings.SEARCH_MAX_PAGES
    else:
        page_count = search_result.data['total'] // per_page or 1
    pagination = [{'number': p + 1} for p in range(page_count)]

    return {
        'current_page': search_result.data['offset'] // per_page + 1,
        'pages': pagination
    }


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
    gfilters = [{
        'type': 'match_all',
        'field_name': name,
        'values': values
    } for name, values in filters.items()]
    result = client.post_search(
        index,
        {
            'q': query,
            'facets': facet_map['facets'],
            'filters': gfilters,
            'offset': (int(page) - 1) * settings.SEARCH_RESULTS_PER_PAGE,
            'limit': settings.SEARCH_RESULTS_PER_PAGE
        })
    search_data = [mdf_to_datacite(r['content'][0], index, r['subject'])
                   for r in result.data['gmeta']]

    facets = result.data.get('facet_results', [])
    # Create a table we can use to lookup facets by name
    fac_lookup = {f['name']: f['field_name'] for f in facet_map['facets']}
    # Set the field_name identifier on each facet
    for facet in facets:
        for bucket in facet['buckets']:
            bucket['field_name'] = fac_lookup[facet['name']]
            filtered_facets = filters.get(bucket['field_name'])
            if filtered_facets and bucket['value'] in filtered_facets:
                bucket['checked'] = True
    return {'search_results': search_data,
            'facets': facets,
            'result': result,
            'pagination': _get_pagination(result)}


def load_search_client(user):
    if user.is_authenticated:
        token = user.social_auth.get(provider='globus')\
            .extra_data['access_token']
        authorizer = globus_sdk.AccessTokenAuthorizer(token)
        return globus_sdk.SearchClient(authorizer=authorizer)
    return globus_sdk.SearchClient()


def map_to_datacite(search_data):
    """Map fields from Globus Search data to Datacite 4.1 fields. Only
    fields that match will be returned and rendered on the search page. The
    settings.SEARCH_FORMAT_FILE is used to match search entries
    """
    with open(settings.SERACH_FORMAT_FILE) as f:
        raw_data = f.read()
        fields = json.loads(raw_data)

    detail_data = {}
    for name, data in fields.items():
        field_name = None
        if name in search_data.keys():
            field_name = name
        if not field_name:
            aliases = set(search_data.keys()) & set(data.get('aliases', []))
            if any(aliases):
                field_name = aliases.pop()
        if field_name:
            detail_data[name] = data.copy()
            detail_data[name]['value'] = search_data[field_name]

    return detail_data


def mdf_to_datacite(data, index, subject):
    """TEST DATA!!! This is used as a stand-in for a Globus Search index
    which has not been setup yet. Once we switch over to the new index,
    this function should be deleted."""
    # General datacite 4.1
    datacite = {
            "alternate_identifiers": data['mdf'].get('scroll_id', ''),
            "contributors": "",
            "creators": "Materials Data Facility",
            "dates": data['mdf']['ingest_date'],
            "descriptions": "",
            "formats": data['mdf'].get('tags'),
            "funding_references": "",
            "geo_locations": "",
            "identifier": data['mdf']['mdf_id'],
            "language": "",
            "publication_year": "",
            "publisher": "",
            "related_identifiers": "",
            "resource_type": "application/json",
            "rights_list": "",
            "sizes": "",
            "subjects": list(data.get('dss_tox', {}).values()),
            "titles": data['mdf']['title'],
            "version": data['mdf']['metadata_version']
    }
    # Custom portal specific data
    portal = {
        'index': index,
        'subject': quote_plus(subject)
    }
    datacite.update(portal)
    return datacite
