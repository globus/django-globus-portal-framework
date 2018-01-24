from django.urls import path
from globus_portal_framework.search.views import index, detail
from globus_portal_framework.search import api

urlpatterns = [
    # We will likely use this at some point
    # path('admin/', admin.site.urls),
    path('api/v1/search/<index>', api.search),
    path('detail/<index>/<path:subject>', detail),
    path('', index)
]
