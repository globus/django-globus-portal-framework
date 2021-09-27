import pytest
from datetime import timedelta
from urllib.parse import urlsplit, parse_qs, unquote_plus

from django.http import HttpResponse
from django.urls import path, reverse, include
from django.utils import timezone

from globus_portal_framework import load_transfer_client, ExpiredGlobusToken


def my_transfer_view(request):
    """A django view that tries to load a transfer client with a user's
    access tokens."""
    resp = HttpResponse('<html><body>Hello Globus!</body></html>')
    load_transfer_client(request.user)
    return resp


urlpatterns = [
    path('my-transfer-view/', my_transfer_view, name='my_transfer_view'),
    path('', include('social_django.urls', namespace='social')),
]


@pytest.mark.urls('tests.test_middleware')
@pytest.mark.django_db
def test_middleware_normal_usage(user, client):
    client.force_login(user)
    r = client.get(reverse('my_transfer_view'))
    assert r.status_code == 200


@pytest.mark.urls('tests.test_middleware')
@pytest.mark.django_db
def test_expired_token_does_redirect(user, client):
    client.force_login(user)
    # Tokens last 48 hours (Mocks are set to this). 72 is good leeway.
    user.last_login = timezone.now() - timedelta(days=3)
    user.save()
    r = client.get(reverse('my_transfer_view'))
    assert r.status_code == 302


@pytest.mark.urls('tests.test_middleware')
@pytest.mark.django_db
def test_expired_token_redirect_handles_params(user, client):
    client.force_login(user)
    # Tokens last 48 hours (Mocks are set to this). 72 is good leeway.
    user.last_login = timezone.now() - timedelta(days=3)
    user.save()
    params = {'transfer': 'globus://myendpoint/file.txt'}
    rurl = '{}?{}'.format(reverse('my_transfer_view'), params)
    r = client.get(rurl)
    assert r.status_code == 302

    next_url = parse_qs(urlsplit(r.url).query)['next'][0]
    next_unquoted = unquote_plus(next_url)
    assert next_unquoted == rurl


@pytest.mark.urls('tests.test_middleware')
@pytest.mark.django_db
def test_no_middleware_raises_exception(user, client, settings):
    settings.MIDDLEWARE = [m for m in settings.MIDDLEWARE
                           if 'ExpiredTokenMiddleware' not in m]
    client.force_login(user)
    # Tokens last 48 hours (Mocks are set to this). 72 is good leeway.
    user.last_login = timezone.now() - timedelta(days=3)
    user.save()
    with pytest.raises(ExpiredGlobusToken):
        client.get(reverse('my_transfer_view'))
