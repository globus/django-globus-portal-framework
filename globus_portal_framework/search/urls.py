from django.urls import path
from globus_portal_framework.search.views import (index, bag_list, bag_create,
                                                  detail,
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
    path('bags/create/', bag_create, name='bag-create'),
    path('bags/', bag_list, name='bag-list'),
    path('detail/<path:subject>/', detail, name='detail'),
    path('', index, name='search')
]
