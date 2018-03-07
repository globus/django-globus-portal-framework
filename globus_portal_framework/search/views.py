from django.shortcuts import render
from globus_portal_framework.search import utils, settings


def index(request):
    """
    Search the index configured in settings.SEARCH_INDEX with the queryparams
    'q' for query, 'filter.<filter>' for facet-filtering, 'page' for pagination
    If the user visits this page again without a search query, we auto search
    for them again using their last query. If the user is logged in, they will
    automatically do a credentialed search for Globus Search to return
    confidential results. If more results than settings.SEARCH_RESULTS_PER_PAGE
    are returned, they are paginated (Globus Search does the pagination, we
    only do the math to calculate the offset).

    Query Params
    q: key words for the users search. Ex: 'q=foo*' will search for 'foo*'

    filter.: Filter results on facets defined in settings.SEARCH_SCHEMA. The
    syntax for filters using query params is:
    '?filter.<filter_type>=<filter_value>, where 'filter.<filter_type>' is
    defined in settings.SEARCH_SCHEMA and <filter_value> is any value returned
    by Globus Search contained within search results. For example, we can
    define a filter 'mdf.elements' in our schema, and use it to filter all
    results containing H (Hydrogen).

    page: Page of the search results. Number of results displayed per page is
    configured in settings.SEARCH_RESULTS_PER_PAGE, and number of pages can be
    controlled with settings.SEARCH_MAX_PAGES.

    Templates:
    The resulting page is templated using the 'search.html' template, and
    'search-results.html' and 'search-facets.html' template components. The
    context required for searches is shown here:

    {
        'search': {
            'facets': [
                {'buckets': [{'field_name': 'mdf.resource_type',
                            'value': 'record'}],
                'name': 'Resource Type'},
                <More Facets>...
            ],
            'pagination': {'current_page': 1, 'pages': [{'number': 1}]},
            'search_results': [
            {
                'subject': '<Globus Search Subject>',
                'fields': {
                    'titles': {'field_name': 'titles',
                                                    'value': '<Result Title>'},
                    'version': {'field_name': 'version', 'value': '0.3.2'},
                    '<field_name>': {'field_name': '<display_name>',
                                     'value': '<field_value>'},
                    'foo_field': {'field_name': 'foo', 'value': 'bar'}
                }
            }, <More Search Results>...]
        }
    }

    Example request:
    http://myhost/?q=foo*&page=2&filter.my.special.filter=goodresults
    """
    context = {}
    query = request.GET.get('q') or request.session.get('query') or \
        settings.DEFAULT_QUERY
    if query:
        filters = {k.replace('filter.', ''): request.GET.getlist(k)
                   for k in request.GET.keys() if k.startswith('filter.')}
        context['search'] = utils.post_search(settings.SEARCH_INDEX, query,
                                              filters,
                                              request.user,
                                              request.GET.get('page', 1))
        request.session['search'] = {
            'query': query,
            'filters': filters,
        }
    return render(request, 'search.html', context)


def detail(request, subject):
    """
    Load a page for showing details for a single search result. The data is
    exactly the same as the entries loaded by the index page in the
    'search_results'. The template is ultimately responsible for which fields
    are displayed. The only real functional difference between the index page
    and the detail page is that it displays only a single result. The
    detail-overview.html template is used to render the page.

    Example request:
    http://myhost/detail/<subject>

    Example context:
    {'subject': '<Globus Search Subject>',
     'fields': {
                'titles': {'field_name': 'titles', 'value': '<Result Title>'},
                'version': {'field_name': 'version', 'value': '0.3.2'},
                '<field_name>': {'field_name': '<display_name>', 'value':
                                                            '<field_value>'}
                }
    }
    """
    return render(request, 'detail-overview.html',
                  utils.get_subject(subject, request.user))


def detail_metadata(request, subject):
    """
    Render a metadata page for a result. This is functionally the same as the
    'detail' page except it renders a detail-metadata.html instead for
    displaying tabular data about an object.
    """
    return render(request, 'detail-metadata.html',
                  utils.get_subject(subject, request.user))
