from unittest import mock

from django.test import TestCase
from django.test.utils import override_settings
from django.test.client import RequestFactory
from django.urls import path

from globus_portal_framework.templatetags.is_active import is_active


def view_simple(request):
    pass


def view_complex(request, sun, moon, stars):
    pass


urlpatterns = [
    path('view-simple', view_simple, name='view-simple'),
    path('view-complex/<int:sun>/<int:moon>/<int:stars>/', view_complex,
         name='view-complex')
]


@override_settings(ROOT_URLCONF=__name__)
class TestTemplateTags(TestCase):

    def setUp(self):
        self.reqf = RequestFactory()

    def test_view_simple(self):
        r = self.reqf.get('/view-simple')
        self.assertEqual(is_active(r, 'view-simple'), 'active')

    def test_is_active_inactivated(self):
        r = self.reqf.get('/view-simple')
        self.assertEqual(is_active(r, 'view-complex'), '')

    def test_is_active_with_kwargs(self):
        r = self.reqf.get('/view-complex/1/2/3/')
        self.assertEqual(is_active(r, 'view-complex', sun=1, moon=2, stars=3),
                         'active')

    @mock.patch('globus_portal_framework.templatetags.is_active.log')
    def test_is_active_quietly_raises_error(self, log):
        r = self.reqf.get('view-complex/1/2/3/')
        self.assertEqual(is_active(r, 'view-complex/', sun=1, moon=2, stars=3),
                         '')
        self.assertTrue(log.error.called)
