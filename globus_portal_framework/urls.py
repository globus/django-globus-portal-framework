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
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.shortcuts import redirect
from globus_portal_framework.views import (
    search, index_selection, search_debug, search_debug_detail,
    detail, detail_transfer, detail_preview
)
from django.contrib.auth import logout
from globus_portal_framework.api import restricted_endpoint_proxy_stream

# search detail for viewing info about a single search result
detail_urlpatterns = [
    path('<index>/detail-preview/<subject>/',
         detail_preview, name='detail-preview'),
    path('<index>/detail-preview/<subject>/<endpoint>/<path:url_path>/',
         detail_preview, name='detail-preview'),
    path('<index>/detail-transfer/<subject>', detail_transfer,
         name='detail-transfer'),
    path('<index>/detail/<subject>/', detail, name='detail'),
    path('<index>/search-debug-detail/<subject>/', search_debug_detail,
         name='search-debug-detail'),
]


# FIXME: Temporary, remove after #55
def dgpf_logout(request):
    logout(request)
    return redirect('/')


urlpatterns = [
    # Proxy remote file requests
    path('api/proxy/', restricted_endpoint_proxy_stream, name='restricted_endpoint_proxy_stream'),
    # Globus search portal. Provides default url '/'.
    path('logout/', dgpf_logout, name='logout'),
    path('', index_selection, name='index-selection'),
    path('<index>/', search, name='search'),
    path('<index>/search-debug/', search_debug, name='search-debug'),
    path('', include(detail_urlpatterns)),
]


# Only include non-globus-portal-framework core URLs in development
if getattr(settings, 'GLOBUS_PORTAL_FRAMEWORK_DEVELOPMENT_APP', False):
    urlpatterns.extend([
        path('admin', admin.site.urls),
        path('', include('social_django.urls', namespace='social')),
        # FIXME Remove after merging #55 python-social-auth-upgrade
        path('', include('django.contrib.auth.urls'))
    ])
