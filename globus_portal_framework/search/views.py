from django.shortcuts import render
from globus_portal_framework.search.utils import load_search_client
from django.conf import settings


def index(request):
    return render(request, 'search.html')


def detail(request, index, subject):
    client = load_search_client(request.user)
    result = client.get_subject(index, subject)
    context = {'result': result.data['content'][0][settings.SEARCH_INDEX]}
    return render(request, 'detail.html', context)
