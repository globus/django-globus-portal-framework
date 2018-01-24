import json
from django.http import JsonResponse

from globus_portal_framework.search.utils import load_search_client


def search(request, index):
    """Supports both authenticated and anonymous searches. See here
    for complex queries:

    **External Documentation**

    See `POST Search Query
    <https://docs.globus.org/api/search/search/#complex_post_query>`_
    in the API documentation for details.
    """
    if not request.body:
        return {}
    client = load_search_client(request.user)
    response = client.post_search(index, json.loads(request.body))
    return JsonResponse(response.data)
