from django.urls import path
from globus_portal_framework.search.views import (index, detail,
                                                  detail_metadata,
                                                  detail_transfer,
                                                  detail_preview)

urlpatterns = [
    # We will likely use this at some point
    # path('admin/', admin.site.urls),
    path('detail-metadata/<path:subject>', detail_metadata,
         name='detail-metadata'),
    path('detail-preview/<path:subject>', detail_preview,
         name='detail-preview'),
    path('detail-transfer/<path:subject>', detail_transfer,
         name='detail-transfer'),
    path('detail/<path:subject>/', detail, name='detail'),
    path('', index, name='search')
]
