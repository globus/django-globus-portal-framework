from django.urls import path
from globus_portal_framework.views import search_debug, search_debug_detail


urlpatterns = [
    path('<index>/search-debug/', search_debug, name='search-debug'),
    path('<index>/search-debug-detail/<subject>/', search_debug_detail,
         name='search-debug-detail'),
]
