from django.urls import path
from globus_portal_framework.globus_search.views import index
from globus_portal_framework.globus_search import api

urlpatterns = [
    # We will likely use this at some point
    # path('admin/', admin.site.urls),
    path('api/v1/search/<index>', api.search),
    path('', index)
]
