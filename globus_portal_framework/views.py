import logging
import os
from urllib.parse import unquote, urlparse, urlencode
from json import dumps
import globus_sdk
from django.shortcuts import render
from django.urls import reverse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from globus_portal_framework import (
    preview, helper_page_transfer, get_helper_page_url, parse_globus_url,
    get_subject, post_search, PreviewException, PreviewURLNotFound,
    ExpiredGlobusToken, check_exists, get_template
)

log = logging.getLogger(__name__)


def index_selection(request):
    context = {'search_indexes': settings.SEARCH_INDEXES}
    return render(request, 'index-selection.html', context)


def search(request, index):
    """
    Search the 'index' with the queryparams 'q' for query, 'filter.<filter>'
    for facet-filtering, 'page' for pagination If the user visits this
    page again without a search query, we auto search for them
    again using their last query. If the user is logged in, they will
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
        context['search'] = post_search(index, query, filters, request.user,
                                        request.GET.get('page', 1))
        request.session['search'] = {
            'full_query': urlparse(request.get_full_path()).query,
            'query': query,
            'filters': filters,
            'index': index,
        }
    return render(request, get_template(index, 'search.html'), context)


def search_debug(request, index):
    context = {}
    query = request.GET.get('q') or '*'
    filters = {k.replace('filter.', ''): request.GET.getlist(k)
               for k in request.GET.keys() if k.startswith('filter.')}
    results = post_search(index, query, filters, request.user, 1)
    context['search'] = results
    context['facets'] = dumps(results['facets'], indent=2)
    return render(request, get_template(index, 'search-debug.html'), context)


def search_debug_detail(request, index, subject):
    sub = get_subject(index, subject, request.user)
    debug_fields = {name: dumps(data, indent=2) for name, data in sub.items()}
    from collections import OrderedDict
    dfields = OrderedDict(debug_fields)
    dfields.move_to_end('all')
    sub['django_portal_framework_debug_fields'] = dfields
    return render(request,
                  get_template(index, 'search-debug-detail.html'), sub)


def detail(request, index, subject):
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
    return render(request, get_template(index, 'detail-overview.html'),
                  get_subject(index, subject, request.user))


def detail_metadata(request, index, subject):
    """
    Render a metadata page for a result. This is functionally the same as the
    'detail' page except it renders a detail-metadata.html instead for
    displaying tabular data about an object.
    """
    return render(request, get_template(index, 'detail-metadata.html'),
                  get_subject(index, subject, request.user))


@csrf_exempt
def detail_transfer(request, index, subject):
    context = get_subject(index, subject, request.user)
    task_url = 'https://www.globus.org/app/activity/{}/overview'
    if request.user.is_authenticated:
        try:
            ep, path = parse_globus_url(unquote(subject))
            check_exists(request.user, ep, path)
            if request.method == 'POST':
                task = helper_page_transfer(request, ep, path,
                                            helper_page_is_dest=True)
                context['transfer_link'] = task_url.format(task['task_id'])
            this_url = reverse('detail-transfer', args=[index, subject])
            full_url = request.build_absolute_uri(this_url)
            # This url will serve as both the POST destination and Cancel URL
            context['helper_page_link'] = get_helper_page_url(
                full_url, full_url, folder_limit=1, file_limit=0)
        except globus_sdk.TransferAPIError as tapie:
            if tapie.code == 'EndpointPermissionDenied':
                messages.error(request, 'You do not have permission to '
                                        'transfer files from this endpoint.')
            elif tapie.code == 'ClientError.NotFound':
                messages.error(request, tapie.message.replace('Directory',
                                                              'File'))
            elif tapie.code == 'AuthenticationFailed' \
                    and tapie.message == 'Token is not active':
                raise ExpiredGlobusToken()
            else:
                log.error('Unexpected Error found during transfer request',
                          tapie)
                messages.error(request, tapie.message)
    return render(request,
                  get_template(index, 'detail-transfer.html'), context)


def detail_preview(request, index, subject, endpoint=None, url_path=None):
    context = get_subject(index, subject, request.user)
    try:
        scope = request.GET.get('scope')
        if not any((endpoint, url_path, scope)):
            log.error('Preview Error: Endpoint, Path, or Scope not given. '
                      '(Got: {}, {}, {})'.format(endpoint, url_path, scope))
            raise PreviewURLNotFound(subject)
        url = 'https://{}{}'.format(endpoint, url_path)
        log.debug('Previewing with url: {}'.format(url))
        context['preview_data'] = \
            preview(request.user, url, scope, settings.PREVIEW_DATA_SIZE)
    except PreviewException as pe:
        if pe.code in ['UnexpectedError', 'ServerError']:
            log.exception(pe)
        log.debug('User error: {}'.format(pe))
        messages.error(request, pe.message)
    return render(request, get_template(index, 'detail-preview.html'), context)
