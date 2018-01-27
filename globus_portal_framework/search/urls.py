from django.urls import path
from globus_portal_framework.search.views import (index, detail, mock_metadata,
                                                  mock_overview)
from globus_portal_framework.search import api

urlpatterns = [
    # We will likely use this at some point
    # path('admin/', admin.site.urls),
    path('api/v1/search/<index>', api.search),
    path('test/overview', mock_overview),
    path('test/metadata', mock_metadata),
    path('detail-metadata/<index>/<path:subject>', mock_metadata,
         name='detail-metadata'),
    path('detail/<index>/<path:subject>', detail, name='detail'),
    path('', index)
]
