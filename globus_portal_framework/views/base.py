import logging
import copy
from urllib.parse import urlparse
from collections import OrderedDict
from json import dumps
import globus_sdk
import django
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
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


def index_selection(request: HttpRequest) -> HttpResponse:
    """
    This is usually the root `/` page for the portal for Globus Portal Framework. Users
    are first directed to this page to choose a Globus Search index. If the portal is
    configured with groups, they may also be prompted to check the groups page to ensure
    they have access to view the portal.

    :param request: The Django request object
    :returns: A rendered Django Template View

    **Templates**:

    Chooses the following templates in order of precedence if they exist, determined
    by ``settings.BASE_TEMPLATES``:

    * ``templates/globus-portal-framework/v2/index-selection.html``
    * *Default DGPF Template*

    **Context**:

    This view creates the following context:

    * ``search_indexes`` - The entire block defined in settings.SEARCH_INDEXES
    * ``allowed_groups`` - The entire block defined in settings.SOCIAL_AUTH_GLOBUS_ALLOWED_GROUPS

    **Context Example**:

    .. code-block:: python

        {
            'allowed_groups': [
                {
                    'name': 'My Group 1',
                    'uuid': '08d8cd36-dd9d-11ee-8849-b93550bcf92a'
                }
            ],
            'search_indexes': {
                'perfdata': {
                    'facets': [...],
                    'fields': [...]
                    'filter_match': 'match-all',
                    'name': 'Performance Data',
                    'template_override_dir': 'perfdata',
                    'uuid': '5e83718e-add0-4f06-a00d-577dc78359bc'
                }
            }
        }

    """
    context = {
        'search_indexes': get_setting('SEARCH_INDEXES'),
        'allowed_groups': getattr(settings,
                                  'SOCIAL_AUTH_GLOBUS_ALLOWED_GROUPS', [])
    }
    return render(request, gsearch.get_template_path('index-selection.html'),
                  context)


def search_about(request: HttpRequest, index: str):
    """
    The Search About view is intended to show basic information about a Globus Search
    Index. It is by default accessible via the search tab located here:

    ``templates/globus-portal-framework/v2/components/search-nav.html``

    :param request: The Django request object
    :param index: The URL string identifying the Search Index
    :returns: A rendered Django Template View

    **Templates**:

    Chooses the following templates in order of precedence if they exist, determined
    by ``settings.BASE_TEMPLATES`` and ``settings.SEARCH_INDEXES.<index>.template_override_dir``
    in :ref:`search_settings_reference`:

    * ``templates/my-index/globus-portal-framework/v2/search-about.html``
    * ``templates/globus-portal-framework/v2/search-about.html``
    * *Default DGPF Template*

    **Context**:

    This view has not context.
    """
    tvers = gsearch.get_template_path('search-about.html', index=index)
    return render(request, gsearch.get_template(index, tvers), {})


def search(request: HttpRequest, index: str) -> HttpResponse:
    """
    Search the 'index' with the queryparams 'q' for query, 'filter.<filter>'
    for facet-filtering, 'page' for pagination If the user visits this
    page again without a search query, we auto search for them
    again using their last query. If the user is logged in, they will
    automatically do a credentialed search for Globus Search to return
    confidential results (results where user is listed within ``visible_to``).
    If more results than settings.SEARCH_RESULTS_PER_PAGE are returned, they
    are paginated.

    :param request: The Django request object
    :param index: The URL string identifying the Search Index
    :returns: A rendered Django Template View

    **Query Params**:

    ``q`` -- key words for the users search. Ex: 'q=foo*' will search for 'foo*'

    ``filter.`` -- Filter results on facets defined in settings.SEARCH_SCHEMA. The
    syntax for filters using query params is:
    '?filter.<filter_type>=<filter_value>, where 'filter.<filter_type>' is
    defined in settings.SEARCH_SCHEMA and <filter_value> is any value returned
    by Globus Search contained within search results. For example, we can
    define a filter 'mdf.elements' in our schema, and use it to filter all
    results containing H (Hydrogen).

    ``page`` -- Page of the search results. Number of results displayed per page is
    configured in settings.SEARCH_RESULTS_PER_PAGE, and number of pages can be
    controlled with settings.SEARCH_MAX_PAGES.

    **Templates**:

    Chooses the following templates in order of precedence if they exist, determined
    by ``settings.BASE_TEMPLATES`` and ``settings.SEARCH_INDEXES.<index>.template_override_dir``
    in :ref:`search_settings_reference`:

    * ``templates/my-index/globus-portal-framework/v2/search.html``
    * ``templates/globus-portal-framework/v2/search.html``
    * *Default DGPF Template*

    **Context** - This view generates the following context:

    * ``count`` The number of search results shown
    * ``offset`` The offset of within the total search results, if the user has attempted to
      view the next page.
    * ``total`` The total results the search returned
    * ``pagination`` A dict containing pagination information about current and available pages
      of search results
    * ``facets`` Facets returned by ``get_search_facets`` in :ref:`gsearch_reference`
      DGPF does extra work to ensure facets are returned in the same order they are
      listed in SEARCH_RESULTS. ``SEARCH_INDEXES.facet_modifiers`` (see :ref:`facet_modifiers`)
      can be used to modify data contained here.
    * ``search_results`` A list of results (controlled by settings.SEARCH_RESULTS_PER_PAGE) which
      contains two additional items for each search result:

            * ``subject``: The Globus Search subject identifying the search result id
            * ``fields``: An object containing DGPF fields (:ref:`configuring_fields`). Raw results are
              always available via `all`.


    .. code-block:: python

        {
            'search': {
                'count': 2,
                'offset': 0,
                'total': 2,
                'pagination': {'current_page': 1, 'pages': [{'number': 1}]},
                'facets': [
                    {'buckets': [{'field_name': 'mdf.resource_type',
                                'value': 'record'}],
                    'name': 'Resource Type'},
                    <More Facets>...
                ],
                'search_results': [
                {
                    'all': [<raw subject>],
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


def detail(request: HttpRequest, index: str, subject: str) ->  django.http.HttpResponse:
    """
    Load a page for showing details for a single search result (subject). This view fetches
    the subject in the URL from Globus Search, and runs it through DGPF Fields (:ref:`configuring_fields`).
    to produce context ready to render. The Detail page is intended to show all information about
    a Globus Search Subject, compared with the search view which is only intended to show minimum relavent
    information and hide unnecessary detail.

    :param request: The Django request object
    :param index: The URL string identifying the Search Index
    :param subject: The Globus Search Subject to be displayed
    :returns: A rendered Django Template View


    **Templates**:

    Chooses the following templates in order of precedence if they exist, determined
    by ``settings.BASE_TEMPLATES`` and ``settings.SEARCH_INDEXES.<index>.template_override_dir``
    in :ref:`search_settings_reference`:

    * ``templates/my-index/globus-portal-framework/v2/detail-overview.html``
    * ``templates/globus-portal-framework/v2/detail-overview.html``
    * *Default DGPF Template*

    **Example Request**:
    ``https://myhost/<myindex>/detail/<subject>/``

    **Context**

    * ``subject`` The quoted subject safe for being included in a URL
    * ``fields`` A dict of all configured fields (:ref:`configuring_fields`).
        * Note: `all` is always included for the raw subject data.

    Example context:

    .. code-block::

        {
            'subject': '<Globus Search Subject>',
            'fields': {
                'all': [<list of raw entries>]
                'titles': {'field_name': 'titles', 'value': '<Result Title>'},
                'version': {'field_name': 'version', 'value': '0.3.2'},
                '<field_name>': {'field_name': '<display_name>', 'value': '<field_value>'}
            }
        }
    """
    tvers = gsearch.get_template_path('detail-overview.html', index=index)
    template = gsearch.get_template(index, tvers)
    return render(request, template, gsearch.get_subject(index, subject,
                                                         request.user))


@csrf_exempt
def detail_transfer(request, index, subject):
    """
    Deprecated. Will be removed in a future version.
    """
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
    """
    Deprecated. Will be removed in a future version.
    """
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


def logout(request: HttpRequest, next: str = '/') -> HttpResponseRedirect:
    """
    Revoke the users tokens and pop their Django session, then redirect
    the user.

    :param request: The Django Request
    :param next: Location the user will be redirected after logout. Defaults to `/`.
        Can be specified by URL parameter or Query Parameter. Query Parameter takes
        precedence.
    :returns: django.http.HttpResponseRedirect
    """
    if request.user.is_authenticated:
        gclients.revoke_globus_tokens(request.user)
        django_logout(request)
    return redirect(request.GET.get('next', next))


def allowed_groups(request: HttpRequest) -> HttpResponse:
    """
    Show available Globus Groups configured in settings.SOCIAL_AUTH_GLOBUS_ALLOWED_GROUPS.

    .. note::

        This view is typically only used when groups are configured. If no groups
        are configured, all users will be allowed access and links to this view will not be
        listed by default (although it is still accessible in the URLs).

    .. warning::

        This view **only** controls access to the portal. Results on Globus Search records
        are controlled via ``visible_to`` per-search-result. Restricting who can login to
        your portal does not stop users from being able to access publicly listed search
        results via another Gloubs Application!

    **Parameters**:

    :param request: The Django Request object
    :returns: A rendered Django Template View

    **Templates**:

    Chooses the following templates in order of precedence if they exist, determined
    by ``settings.BASE_TEMPLATES`` and ``settings.SEARCH_INDEXES.<index>.template_override_dir``
    in :ref:`search_settings_reference`:

    * ``templates/my-index/globus-portal-framework/v2/allowed-groups.html``
    * ``templates/globus-portal-framework/v2/allowed-groups.html``
    * *Default DGPF Template*

    **Context**

    * ``allowed_groups`` -- A list of groups a user must have access to (at least one) to access
        the portal.
            * ``is_member`` -- True if the user is a member of this group
            * ``name`` -- The human readable name of this group
            * ``uuid`` -- The Globus uuid if this group.

    Example context:

    .. code-block::

        {
            'allowed_groups': [
                {
                    'is_member': True,
                    'name': 'My Group 1',
                    'uuid': '08d8cd36-dd9d-11ee-8849-b93550bcf92a'
                }
            ]
        }
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
