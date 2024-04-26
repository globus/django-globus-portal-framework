import logging
import copy
from urllib.parse import urlparse
from collections import OrderedDict
from json import dumps
import globus_sdk
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.defaults import server_error, page_not_found
from django.contrib.auth import logout as django_logout

from globus_portal_framework.apps import get_setting
from globus_portal_framework import (
    gsearch, gclients, gtransfer,
    PreviewException, PreviewURLNotFound,
    ExpiredGlobusToken, GroupsException,
)

log = logging.getLogger(__name__)


def index_selection(request):
    context = {
        'search_indexes': get_setting('SEARCH_INDEXES'),
        'allowed_groups': getattr(settings,
                                  'SOCIAL_AUTH_GLOBUS_ALLOWED_GROUPS', [])
    }
    return render(request, gsearch.get_template_path('index-selection.html'),
                  context)


def search_about(request, index):
    tvers = gsearch.get_template_path('search-about.html', index=index)
    return render(request, gsearch.get_template(index, tvers), {})


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
    query = gsearch.get_search_query(request)
    if query:
        filters = gsearch.get_search_filters(request)
        context['search'] = gsearch.post_search(
            index, query, filters, request.user, request.GET.get('page', 1)
        )
        request.session['search'] = {
            'full_query': urlparse(request.get_full_path()).query,
            'query': query,
            'filters': filters,
            'index': index,
        }
        error = context['search'].get('error')
        if error:
            messages.error(request, error)
    tvers = gsearch.get_template_path('search.html', index=index)
    return render(request, gsearch.get_template(index, tvers), context)


def search_debug(request, index):
    query = gsearch.get_search_query(request)
    filters = gsearch.get_search_filters(request)
    results = gsearch.post_search(index, query, filters, request.user, 1)
    context = {
        'search': results,
        'facets': dumps(results['facets'], indent=2)
    }
    tvers = gsearch.get_template_path('search-debug.html', index=index)
    return render(request, gsearch.get_template(index, tvers), context)


def search_debug_detail(request, index, subject):
    sub = gsearch.get_subject(index, subject, request.user)
    debug_fields = {name: dumps(data, indent=2) for name, data in sub.items()}
    dfields = OrderedDict(debug_fields)
    dfields.move_to_end('all')
    sub['django_portal_framework_debug_fields'] = dfields
    tvers = gsearch.get_template_path('search-debug-detail.html', index=index)
    return render(request, gsearch.get_template(index, tvers), sub)


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
    tvers = gsearch.get_template_path('detail-overview.html', index=index)
    template = gsearch.get_template(index, tvers)
    return render(request, template, gsearch.get_subject(index, subject,
                                                         request.user))


@csrf_exempt
def detail_transfer(request, index, subject):
    context = gsearch.get_subject(index, subject, request.user)
    task_url = 'https://app.globus.org/activity/{}/overview'
    if request.user.is_authenticated:
        try:
            # Hacky, we need to formalize remote file manifests
            if 'remote_file_manifest' not in context.keys():
                raise ValueError('Please add "remote_file_manifest" to '
                                 '"fields" for {} in order to use transfer.'
                                 ''.format(index))
            elif not context.get('remote_file_manifest'):
                raise ValueError('"remote_file_manifest" not found in search '
                                 'metadata for index {}. Cannot start '
                                 'Transfer.'.format(index))
            parsed = urlparse(context['remote_file_manifest'][0]['url'])
            ep, path = parsed.netloc, parsed.path
            # Remove line in version 4 after issue #29 is resolved
            ep = ep.replace(':', '')
            gtransfer.check_exists(request.user, ep, path, raises=True)
            if request.method == 'POST':
                task = gtransfer.helper_page_transfer(request, ep, path,
                                                      helper_page_is_dest=True)
                context['transfer_link'] = task_url.format(task['task_id'])
            this_url = reverse('detail-transfer', args=[index, subject])
            full_url = request.build_absolute_uri(this_url)
            # This url will serve as both the POST destination and Cancel URL
            context['helper_page_link'] = gtransfer.get_helper_page_url(
                full_url, full_url, folder_limit=1, file_limit=0)
        except globus_sdk.TransferAPIError as tapie:
            context['detail_error'] = tapie
            if tapie.code == 'AuthenticationFailed' \
                    and tapie.message == 'Token is not active':
                raise ExpiredGlobusToken()
            elif tapie.code == 'ClientError.NotFound':
                context['detail_error'] = tapie
                log.error('File not found: {}'.format(tapie.message))
            elif tapie.code not in ['EndpointPermissionDenied']:
                log.error('Unexpected Error found during transfer request: {}'
                          ''.format(tapie))
        except ValueError as ve:
            log.error(ve)
    tvers = gsearch.get_template_path('detail-transfer.html', index=index)
    return render(request, gsearch.get_template(index, tvers), context)


def detail_preview(request, index, subject, endpoint=None, url_path=None):
    context = gsearch.get_subject(index, subject, request.user)
    try:
        scope = request.GET.get('scope')
        if not any((endpoint, url_path, scope)):
            log.error('Preview Error: Endpoint, Path, or Scope not given. '
                      '(Got: {}, {}, {})'.format(endpoint, url_path, scope))
            raise PreviewURLNotFound(subject)
        url = 'https://{}/{}'.format(endpoint, url_path)
        log.debug('Previewing with url: {}'.format(url))
        context['preview_data'] = \
            gtransfer.preview(request.user, url, scope,
                              get_setting('PREVIEW_DATA_SIZE'))
    except PreviewException as pe:
        if pe.code in ['UnexpectedError', 'ServerError']:
            log.exception(pe)
        context['detail_error'] = pe
        log.debug('User error: {}'.format(pe))
    tvers = gsearch.get_template_path('detail-preview.html', index=index)
    return render(request, gsearch.get_template(index, tvers), context)


def logout(request, next='/'):
    """
    Revoke the users tokens and pop their Django session. Users will be
    redirected to the query parameter 'next' if it is present. If the 'next'
    query parameter 'next' is not present, the parameter next will be used
    instead.
    """
    if request.user.is_authenticated:
        gclients.revoke_globus_tokens(request.user)
        django_logout(request)
    return redirect(request.GET.get('next', next))


def allowed_groups(request):
    """
    The groups view shows a user a list of groups that can be used to request
    access to the server, if using SOCIAL_AUTH_GLOBUS_GROUPS_ALLOWED.
    SOCIAL_AUTH_GLOBUS_GROUPS_ALLOWED prevents access to authenticated
    resources globally unless a user is within the groups allowed.

    Note: This is different than securing the visible_to field on Globus Search
    records. Users may not even login unless they are in the allowlist. If a
    user is allowlist and able to login, they still may not be able to view
    records in Globus Search if the Globus Search records are configured with
    a different group on the records' visible_to.
    """
    # Get the local portal allowlist. If there isn't a setting on the local
    # portal, don't restrict users. Copy the list so we can modify it.
    portal_groups = getattr(settings, 'SOCIAL_AUTH_GLOBUS_ALLOWED_GROUPS', [])
    context = {'allowed_groups': copy.deepcopy(portal_groups)}
    if request.user.is_authenticated:
        try:
            groups_client = gclients.load_globus_client(
                    request.user,
                    globus_sdk.GroupsClient,
                    'groups.api.globus.org',
                    require_authorized=True
            )
            user_groups = {
                g['id']: g for g in groups_client.get_my_groups()
            }
            for group in context['allowed_groups']:
                if user_groups.get(group['uuid']):
                    group['is_member'] = True
        except GroupsException as ge:
            log.exception(ge)
            messages.error(request, 'Error: Unable to fetch Globus Groups')
    tvers = gsearch.get_template_path('allowed-groups.html')
    return render(request, tvers, context)


def handler404(*args, **kwargs):
    log.warning('"globus_portal_framework.views.handler404" is deprecated and '
                'will be removed in version 0.4.0. Please unset or use '
                '"django.views.defaults.page_not_found" instead')
    return page_not_found(*args, **kwargs)


def handler500(*args, **kwargs):
    log.warning('"globus_portal_framework.views.handler500" is deprecated and '
                'will be removed in version 0.4.0. Please unset or use '
                '"django.views.defaults.server_error" instead')
    return server_error(*args, **kwargs)
