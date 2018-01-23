from django.shortcuts import render
from globus_portal_framework.globus_search.utils import load_search_client


def index(request):
    return render(request, 'search.html')


def result_detail(request, index, subject):
    client = load_search_client(request.user)
    result = client.get_subject(index, subject)
    context = {'result': result.data['content'][0]['mdf']}
    return render(request, 'result-detail.html', context)
