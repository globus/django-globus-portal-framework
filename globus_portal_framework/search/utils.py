import json
import globus_sdk

from django.conf import settings


def load_json_file(filename):
    with open(filename) as f:
        raw_data = f.read()
        return json.loads(raw_data)


def search(index, query, facet_filter, user=None):
    """Perform a search and return the relevant data for display to the user.
    Returns a dict with search info stripped, containing only two relavent
    fields:

    {
        'search_results': [{'title': 'My title'...} ...],
        'facets': [{'name': 'myfacet', 'buckets': { ... }, ... ]
    }

    See Search docs here:
    https://docs.globus.org/api/search/schemas/GSearchRequest/
    """
    if not index or not query:
        return {'search_results': [], 'facets': []}
    client = load_search_client(user)
    facet_map = load_json_file(settings.SEARCH_SCHEMA)
    result = client.post_search(index, {'q': query,
                                        'facets': facet_map['facets']})
    search_data = [mdf_to_datacite(r['content'][0])
                   for r in result.data['gmeta']]
    return {'search_results': search_data,
            'facets': result.data.get('facet_results', [])
            }


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


def mdf_to_datacite(data):
    """TEST DATA!!! This is used as a stand-in for a Globus Search index
    which has not been setup yet. Once we switch over to the new index,
    this function should be deleted."""
    return {
            "alternate_identifiers": data['mdf'].get('scroll_id', ''),
            "contributors": "",
            "creators": "Materials Data Facility",
            "dates": data['mdf']['ingest_date'],
            "descriptions": "",
            "formats": data['mdf']['tags'],
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
