import sys
from unittest import mock

from django.test import TestCase, Client
from django.test.utils import override_settings
from django.urls import reverse, path
from django.http import HttpResponse

from globus_portal_framework.tests import test_gsearch, MOCK_RESULT
from globus_portal_framework.tests.mocks import rebuild_index_urlpatterns

from globus_portal_framework.urls import (search_urlpatterns,
                                          register_custom_index,
                                          urlpatterns as dgpf_urlpatterns)
thismodule = sys.modules[__name__]


class MockSearchGetSubject:
    def __init__(self):
        self.data = test_gsearch.get_mock_data(MOCK_RESULT)


SEARCH_INDEXES = {
    'myindex': {
        # Randomly generated and not real
        'uuid': '1e0be00f-8156-499e-980d-f7fb26157c02'
    },
    'my_custom_index': {
        # Randomly generated and not real
        'uuid': '1e0be00f-8156-499e-980d-f7fb26157c02'
    }
}


@override_settings(SEARCH_INDEXES=SEARCH_INDEXES, ROOT_URLCONF=__name__)
class CustomViewsTest(TestCase):

    def setUp(self):
        self.c = Client()
        # Mock endpoint for transfer and preview (Globus HTTPS)

        register_custom_index('my_custom_index', ['my_custom_index'])

        urlpatterns = rebuild_index_urlpatterns(
            search_urlpatterns + dgpf_urlpatterns,
            list(SEARCH_INDEXES.keys()))
        self.custom_search = mock.Mock(
            return_value=HttpResponse('custom_search_view'))
        custom_path = path('<my_custom_index:index>/', self.custom_search,
                           name='search')
        urlpatterns.insert(0, custom_path)
        setattr(thismodule, 'urlpatterns', urlpatterns)

    @mock.patch('globus_portal_framework.views.post_search')
    def test_custom_search_view(self, post_search):
        post_search.return_value = {}
        r = self.c.get(reverse('search', args=['my_custom_index']))
        self.assertEqual(r.status_code, 200)
        self.assertTrue(self.custom_search.called)
        self.assertEqual(r.content, b'custom_search_view')

    @mock.patch('globus_portal_framework.views.post_search')
    def test_regular_search_view_not_affected(self, post_search):
        post_search.return_value = {}
        r = self.c.get(reverse('search', args=['myindex']))
        self.assertEqual(r.status_code, 200)
        self.assertFalse(self.custom_search.called)
        self.assertNotEqual(r.content, b'custom_search_view')
