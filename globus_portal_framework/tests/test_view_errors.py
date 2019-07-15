from unittest import mock

from django.test import SimpleTestCase, override_settings
from django.urls import path

from globus_portal_framework.urls import urlpatterns
from globus_portal_framework.views import handler500, handler404


urlpatterns += [
    path('not-a-real-page', handler404),
    path('exception-view/', handler500)
]


@override_settings(ROOT_URLCONF=__name__)
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

    @mock.patch('globus_portal_framework.views.log')
    def test_500_logs_exception(self, log):
        handler500(self.client.get('/exception-view/'), Exception())
        self.assertTrue(log.exception.called)
