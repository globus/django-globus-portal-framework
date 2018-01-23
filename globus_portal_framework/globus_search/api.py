import json
from django.http import JsonResponse

from globus_portal_framework.globus_search.utils import load_search_client


def search(request, index='mdf', q=''):
    client = load_search_client(request.user)
    data = {}

    if request.method == 'GET':
        data = client.search(index, q)
    elif request.method == 'POST':
        response = client.post_search(index, json.loads(request.body))
        data = response.data

    return JsonResponse(data)
