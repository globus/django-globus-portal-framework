import sys
from urllib.parse import quote_plus

from django.test import TestCase, Client
from django.test.utils import override_settings

from globus_portal_framework.tests.mocks import rebuild_index_urlpatterns

from globus_portal_framework.urls import (search_urlpatterns,
                                          register_custom_index,
                                          urlpatterns as dgpf_urlpatterns)
from globus_portal_framework.exc import IndexNotFound

SEARCH_INDEXES = {'myindex': {
    # Randomly generated and not real
    'uuid': '1e0be00f-8156-499e-980d-f7fb26157c02'
}}

thismodule = sys.modules[__name__]


@override_settings(SEARCH_INDEXES=SEARCH_INDEXES, ROOT_URLCONF=__name__)
class SearchViewsTest(TestCase):

    def setUp(self):
        self.c = Client()
        # Mock endpoint for transfer and preview (Globus HTTPS)
        self.foo_ep = 'eae9d78d-b353-4fa7-9dbe-c60d681bc783'
        # A valid subject url given our views
        self.subject_url = quote_plus('globus://{}/{}'.format(self.foo_ep,
                                                              'foo'))
        # Setup tests so our urlpatterns contain the indexes in SEARCH_INDEXES
        # defined above.
        urlpatterns = rebuild_index_urlpatterns(
            search_urlpatterns + dgpf_urlpatterns,
            list(SEARCH_INDEXES.keys()))
        setattr(thismodule, 'urlpatterns', urlpatterns)

    def test_register_non_existant_index_raises_error(self):
        with self.assertRaises(IndexNotFound):
            register_custom_index('foo', ['bar'])
