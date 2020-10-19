import logging

log = logging.getLogger(__name__)


def drop_empty(facets):
    """Prevent any 'bucket' type facets from being displayed on the portal
    if the buckets contain no data. This also preserves backwards
    compatibility for v0.3.x"""
    return [facet for facet in facets if facet.get('buckets') != []]


def reverse(facets):
    """Reverse the order all facets are displayed"""
    for facet in facets:
        if facet.get('buckets'):
            facet['buckets'].reverse()
    return facets


def sort_terms(facets):
    """Sort terms lexicographically instead of by the number of results
    returned. This will only sort 'terms' type facets."""
    for facet in facets:
        if facet['type'] == 'terms' and facet.get('buckets'):
            facet['buckets'].sort(key=lambda x: x['value'])
    return facets


def sort_terms_numerically(facets):
    """For terms that are all numerical, sort by numeric value. Only
    applies to 'terms' type facets, and facets that contain only numbers
    in their buckets."""
    for facet in facets:
        if facet['type'] == 'terms' and facet.get('buckets'):
            try:
                facet['buckets'].sort(key=lambda x: float(x['value']))
            except ValueError:
                pass
    return facets
