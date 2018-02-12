from django.urls import path
from globus_portal_framework.search.views import (index, detail, mock_metadata)

urlpatterns = [
    # We will likely use this at some point
    # path('admin/', admin.site.urls),
    path('detail-metadata/<path:subject>', mock_metadata,
         name='detail-metadata'),
    path('detail/<path:subject>', detail, name='detail'),
    path('', index, name='search')
]
