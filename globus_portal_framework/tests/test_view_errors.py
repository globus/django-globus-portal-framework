from unittest import mock

from django.test import SimpleTestCase, override_settings
from django.urls import path
from django.views.defaults import server_error

from globus_portal_framework.urls import urlpatterns

urlpatterns += [
    path('exception-view/', server_error)
]


@override_settings(ROOT_URLCONF=__name__, DEBUG=False)
class CustomErrorHandlerTests(SimpleTestCase):

    @mock.patch('globus_portal_framework.views.log', mock.Mock())
    def test_404_handler(self):
        response = self.client.get('/not-a-real-page/')
        # Make assertions on the response here. For example:
        self.assertContains(response, "This page doesn't exist.",
                            status_code=404)

    def test_500_handler(self):
        response = self.client.get('/exception-view/')
        # Make assertions on the response here. For example:
        self.assertContains(response, "That's an error.", status_code=500)
