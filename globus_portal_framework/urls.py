"""globus_portal_framework URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import logging
from django.contrib import admin
from django.urls import path, include, register_converter
from django.conf import settings
from globus_portal_framework.views import (
    search, index_selection, detail, detail_transfer, detail_preview, logout,
    allowed_groups, search_about,
)
from globus_portal_framework.apps import get_setting
from globus_portal_framework.api import restricted_endpoint_proxy_stream
from globus_portal_framework.exc import IndexNotFound


log = logging.getLogger(__name__)


class IndexConverter:

    def __init__(self):
        log.warning('Deprecation Warning: The IndexConverter class will be '
                    'removed in the next version. Please use '
                    'globus_portal_framework.urls.register_custom_index '
                    'instead.')

    @property
    def regex(self):
        """Allowing the regex to be a property makes it more flexible in
        testing, allowing urlpatterns to be rebuilt for test indexes."""
        return '({})'.format('|'.join(settings.SEARCH_INDEXES.keys()))

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value


def register_custom_index(name, match_list):
    """Register a new index converter for a list of names. This is handy if
    you have two or more indices that use the same views. You can then specify
    URLs which will ONLY match the list you provide, and won't steal URLs from
    other indices.

    Examples:
      register_index_converter('tabbed-project', ['myproject1', 'myproject2'])
    In the example above, myproject1 and myproject2 can be routed for custom
    views without stealing views from myproject3. URLs could then look like:

    urlpatterns = [
        path('<tabbed-project:index>/search/', search, name='tp-search'),
    ]

    This example defines a custom search for myproject1 and myproject2 but NOT
    myproject3, myproject4, etc. Anything that does not match the list will
    simply fall through.
    """
    for index in match_list:
        if index not in get_setting('SEARCH_INDEXES').keys():
            raise IndexNotFound(index)

    class CustomIndexConverter:

        @property
        def regex(self):
            return '({})'.format('|'.join(match_list))

        def to_python(self, value):
            return value

        def to_url(self, value):
            return value

    register_converter(CustomIndexConverter, name)


register_custom_index('index', list(get_setting('SEARCH_INDEXES').keys()))

# search detail for viewing info about a single search result
search_urlpatterns = [
    path('<index:index>/about/', search_about, name='search-about'),
    path('<index:index>/', search, name='search'),
    path('<index:index>/detail-preview/<subject>/',
         detail_preview, name='detail-preview'),
    path('<index:index>/detail-preview/<subject>/<endpoint>/<path:url_path>/',
         detail_preview, name='detail-preview'),
    path('<index:index>/detail-transfer/<subject>', detail_transfer,
         name='detail-transfer'),
    path('<index:index>/detail/<subject>/', detail, name='detail'),
    path('allowed-groups/', allowed_groups, name='allowed-groups'),
    # Globus search portal. Provides default url '/'.
    path('', index_selection, name='index-selection'),
]

urlpatterns = [
    # Proxy remote file requests
    path('api/proxy/', restricted_endpoint_proxy_stream,
         name='restricted_endpoint_proxy_stream'),
    path('logout/', logout, name='logout'),
    path('', include(search_urlpatterns)),
]


# Only include non-globus-portal-framework core URLs in development
if getattr(settings, 'GLOBUS_PORTAL_FRAMEWORK_DEVELOPMENT_APP', False):
    urlpatterns.extend([
        path('admin', admin.site.urls),
        path('', include('social_django.urls', namespace='social')),
        path('', include('globus_portal_framework.urls_debugging'))
    ])
