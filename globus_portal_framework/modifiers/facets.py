

def drop_empty(facets):
    """Prevent any 'bucket' type facets from being displayed on the portal
    if the buckets contain no data. This also preserves backwards
    compatibility for v0.3.x"""
    return [facet for facet in facets if facet.get('buckets') != []]
