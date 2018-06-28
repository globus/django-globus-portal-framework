import logging
from os.path import basename
from urllib.parse import unquote, urlparse
import globus_sdk
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from globus_portal_framework.search import settings
from globus_portal_framework.transfer import settings as t_settings
from globus_portal_framework import (preview, helper_page_transfer,
                                     get_helper_page_url, parse_globus_url,
                                     get_subject, post_search,
                                     PreviewException, PreviewURLNotFound,
                                     ExpiredGlobusToken,
                                     check_exists, load_globus_access_token)
from globus_portal_framework.search.models import Minid
from concierge.api import create_bag

log = logging.getLogger(__name__)


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
    query, filters, page = get_search_query_params(request)
    query = query or request.session.get('query') or settings.DEFAULT_QUERY
    context = {}

    if query:
        context['search'] = post_search(settings.SEARCH_INDEX, query, filters,
                                        request.user, page)
        request.session['search'] = {
            'full_query': urlparse(request.get_full_path()).query,
            'query': query,
            'filters': filters,
        }
    return render(request, 'search.html', context)


def get_search_query_params(request):
    query = request.GET.get('q')
    filters = {k.replace('filter.', ''): request.GET.getlist(k)
               for k in request.GET.keys() if k.startswith('filter.')}
    page = request.GET.get('page', 1)
    log.debug('Query: {}, Filters: {}, Page: {}'.format(query, filters, page))
    return query, filters, page


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
                  get_subject(subject, request.user))


def detail_metadata(request, subject):
    """
    Render a metadata page for a result. This is functionally the same as the
    'detail' page except it renders a detail-metadata.html instead for
    displaying tabular data about an object.
    """
    return render(request, 'detail-metadata.html',
                  get_subject(subject, request.user))


@csrf_exempt
def detail_transfer(request, subject):
    context = get_subject(subject, request.user)
    task_url = 'https://www.globus.org/app/activity/{}/overview'
    if request.user.is_authenticated:
        try:
            ep, path = parse_globus_url(unquote(subject))
            check_exists(request.user, ep, path)
            if request.method == 'POST':
                task = helper_page_transfer(request, ep, path,
                                            helper_page_is_dest=True)
                context['transfer_link'] = task_url.format(task['task_id'])
            this_url = reverse('detail-transfer', args=[subject])
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
    return render(request, 'detail-transfer.html', context)


def detail_preview(request, subject):
    context = get_subject(subject, request.user)
    try:
        url, scope = context['service'].get('globus_http_link'), \
                     context['service'].get('globus_http_scope')
        # TODO: DEPRECATED -- Remove this "elif" block at version 0.3.0
        if (not url or not scope) and (t_settings.GLOBUS_HTTP_ENDPOINT and
                                       t_settings.PREVIEW_TOKEN_NAME):
            _, path = parse_globus_url(unquote(subject))
            context['subject_title'] = basename(path)
            url = '{}{}'.format(t_settings.GLOBUS_HTTP_ENDPOINT, path)
            scope = t_settings.PREVIEW_TOKEN_NAME
            log.warning(
                'settings.GLOBUS_HTTP_ENDPOINT and settings.PREVIEW_TOKEN_NAME'
                ' are deprecated and will be removed in a future version. '
                'Please instead retrieve the URL from the search result under '
                'the key defined by "globus_http_link" and "globus_http_scope"'
                ' in settings.ENTRY_SERVICE_VARS')
        if not url or not scope:
            log.debug('Preview URL or Scope not found. Searched '
                      'entry {} using settings.ENTRY_SERVICE_VARS, result: {}'
                      ''.format(url, scope, subject, context['service']))
            raise PreviewURLNotFound(subject)
        context['preview_data'] = \
            preview(request.user, url, scope, t_settings.PREVIEW_DATA_SIZE)
    except PreviewException as pe:
        if pe.code in ['UnexpectedError', 'ServerError']:
            log.error(pe)
        log.debug('User error: {}'.format(pe))
        messages.error(request, pe.message)
    return render(request, 'detail-preview.html', context)


def bag_create(request):
    if request.method == 'GET':
        context = {}
        query, filters, page = get_search_query_params(request)
        context['search'] = post_search(settings.SEARCH_INDEX, query, filters,
                                        request.user, limit=settings.BAG_LIMIT)
        log.debug(context['search']['search_results'][0]['service'].keys())

        rfm_lists = [sr['service']['remote_file_manifest']
            for sr in context['search']['search_results']]
        flat_rfm_list = [item for sublist in rfm_lists for item in sublist]

        log.debug('{} result candidates for bag creation'.format(
            len(context['search']['search_results'])))
        request.session['candidate_bags'] = flat_rfm_list
        request.session.modified = True
        # log.debug(context['search']['search_results'][0]['service'])
        return render(request, 'bag-create.html', context)
    if request.method == 'POST':
        bag_title = request.POST.get('bag-name')
        rfm_urls = request.POST.getlist('rfm-urls')
        can_bags = request.session.get('candidate_bags')
        if not can_bags or not rfm_urls or not bag_title:
            log.error('Error creating a bag. Bag name "{}", Session stored '
                      'manifests ({}), or user chosen bag urls ({}) were empty'
                      ''.format(bag_title, len(can_bags), len(rfm_urls)))
            messages.error(request, 'There was an error creating your bag, '
                                    'please contact your system administrator.'
                           )
            return redirect('bag-list')
        del request.session['candidate_bags']


        manifests = [b for b in can_bags if b['url'] in rfm_urls]
        tok = load_globus_access_token(request.user, 'auth.globus.org')
        resp = create_bag('https://concierge.fair-research.org', manifests,
                           request.user.get_full_name(), request.user.email,
                           bag_title, tok)
        minid = Minid(id=resp['minid_id'], user=request.user)
        minid.save()
        messages.info(request, 'Your bag {} has been created with {} files.'
                      ''.format(minid.id, len(manifests)))
        return redirect('bag-list')


def bag_list(request):
    context = {'bags': Minid.objects.filter(users=request.user)}
    return render(request, 'bag-list.html', context)
