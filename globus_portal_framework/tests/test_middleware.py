from datetime import timedelta

from django.test import TestCase, Client
from django.test.utils import override_settings
from django.http import HttpResponse
from django.urls import path, reverse
from django.utils import timezone

from globus_portal_framework import load_transfer_client, ExpiredGlobusToken
from globus_portal_framework.tests.mocks import get_logged_in_client


def my_transfer_view(request):
    """A django view that tries to load a transfer client with a user's
    access tokens."""
    resp = HttpResponse('<html><body>Hello Globus!</body></html>')
    load_transfer_client(request.user)
    return resp

urlpatterns = [
    path('', my_transfer_view, name='my_transfer_view')
]

T_MIDDLEWARE = 'globus_portal_framework.middleware.ExpiredTokenMiddleware'


class TestExpiredTokensMiddleware(TestCase):

    def setUp(self):
        self.c, self.user = get_logged_in_client('bob',
                                                 ['transfer.api.globus.org'])

    @override_settings(ROOT_URLCONF=__name__)
    def test_middleware_normal_usage(self):
        with self.modify_settings(MIDDLEWARE={'append': T_MIDDLEWARE}):
            r = self.c.get(reverse('my_transfer_view'))
            self.assertEqual(r.status_code, 200)

    @override_settings(ROOT_URLCONF=__name__, SESSION_COOKIE_AGE=9999999999)
    def test_expired_token_does_redirect(self):
        # Tokens last 48 hours (Mocks are set to this). 72 is good leeway.
        self.user.last_login = timezone.now() - timedelta(days=3)
        self.user.save()
        with self.modify_settings(MIDDLEWARE={'append': T_MIDDLEWARE}):
            r = self.c.get(reverse('my_transfer_view'))
            self.assertEqual(r.status_code, 302)

    @override_settings(ROOT_URLCONF=__name__, SESSION_COOKIE_AGE=9999999999)
    def test_no_middleware_raises_exception(self):
        # Tokens last 48 hours (Mocks are set to this). 72 is good leeway.
        self.user.last_login = timezone.now() - timedelta(days=3)
        self.user.save()
        with self.modify_settings(MIDDLEWARE={'remove': T_MIDDLEWARE}):
            with self.assertRaises(ExpiredGlobusToken):
                self.c.get(reverse('my_transfer_view'))
