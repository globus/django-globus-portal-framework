import json
from six.moves.urllib.parse import unquote
from django.shortcuts import render
from globus_portal_framework.search import utils
from django.conf import settings


def index(request):
    context = {}
    query = request.GET.get('q') or request.session.get('query')
    if query:
        filters = {k.replace('filter.', ''): request.GET.getlist(k)
                   for k in request.GET.keys() if k.startswith('filter.')}
        context['search'] = utils.search(settings.SEARCH_INDEX, query, filters,
                                         request.user,
                                         request.GET.get('page', 1))
        request.session['search'] = {
            'query': query,
            'filters': filters,
        }
    return render(request, 'search.html', context)


def mock_overview(request, subject='bar'):
    filename = 'globus_portal_framework/search/data/mock-detail-overview.json'
    with open(filename) as f:
        data = json.loads(f.read())
        detail_data = utils.default_search_mapper(data)
        return render(request, 'detail-overview.html',
                      {'detail_data': detail_data,
                       'subject': subject})


def mock_metadata(request, subject='bar'):
    filename = 'globus_portal_framework/search/data/mock-detail-metadata.json'
    with open(filename) as f:
        data = json.loads(f.read())
        context = {'table_head': data['headers'],
                   'table_body': data['body'],
                   'subject': subject}

        return render(request, 'detail-metadata.html', context)


def detail(request, subject):
    """
    Load a page for showing details for a single search result.
    Context for the fields must be provided, an example is as follows:
    {
        'fields':
            {'datacite_field':
                {'name': 'datacite_field', 'value': 'myid'},
            },
            <more fields>
        'subject': 'unique_identifier'
    }
    """
    client = utils.load_search_client(request.user)
    result = client.get_subject(settings.SEARCH_INDEX, unquote(subject))
    context = utils.process_search_data([result.data])[0]
    return render(request, 'detail-overview.html', context)
