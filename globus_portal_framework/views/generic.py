import logging
from urllib.parse import urlparse
from django.views.generic import View
from django.conf import settings
from django.shortcuts import render
from django.contrib import messages
from globus_portal_framework.gsearch import (
    get_template, get_search_filters, get_facets,
    get_search_query, process_search_data, get_index, prepare_search_facets,
    get_pagination, get_subject,
    )
from globus_portal_framework.gclients import (
    load_search_client
)
import globus_portal_framework.exc


log = logging.getLogger(__name__)


class SearchView(View):
    """
    Customize components of a search during different phases of receiving a
    request from a user to rendering a template. This is a handy class to
    customize if you want to modify the request sent to Globus Search, or
    customize the data received by Globus Search before it is rendered on the
    page.

    See post_search for customizing the result before it is sent to Globus
    Search.

    See process_result to override how the result is processed before it is
    rendered by the template.
    """

    DEFAULT_TEMPLATE = 'globus-portal-framework/v2/search.html'

    def __init__(self, template=None, results_per_page=10):
        super().__init__()
        self.template = template or self.DEFAULT_TEMPLATE
        self.results_per_page = results_per_page

    @property
    def query(self):
        return get_search_query(self.request)

    @property
    def filters(self):
        return get_search_filters(self.request)

    @property
    def facets(self):
        index = self.kwargs.get('index')
        if index:
            return prepare_search_facets(get_index(index).get('facets'))
        return []

    @property
    def page(self):
        return self.request.GET.get('page', 1)

    @property
    def offset(self):
        """Get the calculated offset based on the page number and configured
        results-per-page. This value is sent in the request to Globus Search"""
        return (int(self.page) - 1) * self.results_per_page

    @property
    def sort(self):
        return self.get_index_info().get('sort', [])

    def get_index_info(self, index_uuid=None):
        """Fetch info on an index defined in settings.py"""
        return get_index(index_uuid or self.kwargs.get('index'))

    def get_search_client(self):
        return load_search_client(self.request.user)

    def post_search(self, client, index_uuid, search_client_data):
        """If you want to inject or modify any parameters in the
        globus_sdk.SearchClient.post_search function, you can override this
        function. """
        return client.post_search(index_uuid, search_client_data)

    def set_search_session_data(self, index):
        """Set some metadata about the search in the user's session. This will
        record some data about their last search to fill in some basic DGPF
        context, such as the 'Back To Search' link on a result detail page.
        """
        self.request.session['search'] = {
            'full_query': urlparse(self.request.get_full_path()).query,
            'query': self.query,
            'filters': self.filters,
            'index': index,
        }

    def process_result(self, index_info, search_result):
        """
        Process the result from Globus Search into data ready to be rendered
        into search templates.
        """
        return {
            'search': {
                'search_results': process_search_data(
                    index_info.get('fields', []), search_result.data['gmeta']),
                'facets': get_facets(
                    search_result, index_info.get('facets', []), self.filters,
                    index_info.get('filter_match'),
                    index_info.get('facet_modifiers')),
                'pagination': get_pagination(
                    search_result.data['total'], search_result.data['offset']),
                'count': search_result.data['count'],
                'offset': search_result.data['offset'],
                'total': search_result.data['total'],
            }
        }

    def get_context_data(self, index):
        """calls post_search and process_result. If there is an error, returns
        a context with a single 'error' var and logs the exception."""
        data = {
            'q': self.query,
            'filters': self.filters,
            'facets': self.facets,
            'offset': self.offset,
            'sort': self.sort,
            'limit': self.results_per_page,
        }
        try:
            index_info = self.get_index_info(index)
            result = self.post_search(self.get_search_client(),
                                      index_info['uuid'], data)
            return self.process_result(index_info, result)
        except globus_portal_framework.exc.ExpiredGlobusToken:
            # Don't catch this exception. Middleware will automatically
            # redirect the user to login again for fresh tokens.
            raise
        except Exception as e:
            if settings.DEBUG:
                raise
            log.exception(e)
        return {'error': 'There was an error in your search, please try a '
                         'different query or contact your administrator.'}

    def get(self, request, index, *args, **kwargs):
        """
        Fetches the context, then renders a page. Calls 'get_template', which
        checks to see if there is an overridden page for a given index. If
        there is, that is used instead. Otherwise, standard Django template
        precedence loading is used.

        If there is an error, a Django message is sent which can be rendered
        by templates that support them.
        """
        context = self.get_context_data(index)
        self.set_search_session_data(index)
        error = context.get('error')
        if error:
            messages.error(request, error)
        template = get_template(index, self.template)
        log.debug(f'Using template {template}')
        return render(request, template, context)


class DetailView(View):
    DEFAULT_TEMPLATE = 'globus-portal-framework/v2/detail-overview.html'

    def __init__(self, template=None):
        super().__init__()
        self.template = template or self.DEFAULT_TEMPLATE

    def get_context_data(self, index, subject):
        return get_subject(index, subject, self.request.user)

    def get(self, request, index, subject):
        context = self.get_context_data(index, subject)
        return render(request, get_template(index, self.template), context)
