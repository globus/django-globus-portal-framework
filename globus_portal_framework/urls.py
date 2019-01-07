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
from globus_portal_framework.views import (
    search, index_selection, search_debug, search_debug_detail,
    detail, detail_transfer, detail_preview
)
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

urlpatterns = [
    path('admin/', admin.site.urls),
    # Social auth provides /login /logout. Provides no default urls
    path('', include('social_django.urls')),
    path('', include('django.contrib.auth.urls')),

    # Proxy remote file requests
    path('api/proxy/', restricted_endpoint_proxy_stream, name='restricted_endpoint_proxy_stream'),

    # Globus search portal. Provides default url '/'.
    path('', index_selection, name='index-selection'),
    path('<index>/', search, name='search'),
    path('<index>/search-debug/', search_debug, name='search-debug'),
    path('', include(detail_urlpatterns))
]
