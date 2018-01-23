from django.shortcuts import render
from globus_portal_framework.globus_search.utils import load_search_client


def index(request):
    context = {'user': 'anonymous'}
    return render(request, 'search.html', context)


def result_detail(request, index, subject):
    client = load_search_client()
    result = client.get_subject(index, subject)
    context = {'result': result.data['content'][0]['mdf']}
    return render(request, 'result-detail.html', context)
