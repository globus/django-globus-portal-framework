import pytest
from unittest import mock
from datetime import timedelta
import requests
import globus_sdk

from django.contrib.auth.models import AnonymousUser
from django.utils import timezone

from globus_portal_framework.gclients import (
    load_globus_client, load_search_client, load_transfer_client,
    revoke_globus_tokens, get_user_groups
)
from globus_portal_framework import (
    ExpiredGlobusToken, GroupsException, PortalAuthException
)

from tests.mocks import mock_user


@pytest.fixture
def requests_get(monkeypatch):
    """NOTE! This should go away in the next version, it was only used when
    Groups had to be a request outside of the Globus SDK"""
    monkeypatch.setattr(requests, 'get', mock.Mock())
    return requests.get


def test_load_globus_client_with_anonymous_user(search_client):
    load_globus_client(AnonymousUser(), globus_sdk.SearchClient,
                       'search.api.globus.org')
    args, kwargs = search_client.call_args
    assert 'authorizer' not in kwargs


@pytest.mark.django_db
def test_load_globus_client_with_real_user(search_client):
    user = mock_user('bob', ['search.api.globus.org'])
    load_globus_client(user, globus_sdk.SearchClient, 'search.api.globus.org')
    args, kwargs = search_client.call_args
    assert 'authorizer' in kwargs


@pytest.mark.django_db
def test_load_globus_client_with_bad_token(search_client):
    user = mock_user('bob', ['transfer.api.globus.org'])
    with pytest.raises(ValueError):
        load_globus_client(user, globus_sdk.SearchClient,
                           'search.api.globus.org')


def test_load_search_client_with_anonymous_user(search_client):
    load_search_client(AnonymousUser())
    args, kwargs = search_client.call_args
    assert 'authorizer' not in kwargs


@pytest.mark.django_db
def test_load_search_client_with_real_user(search_client):
    user = mock_user('bob', ['search.api.globus.org'])
    load_search_client(user)
    args, kwargs = search_client.call_args
    assert 'authorizer' in kwargs


@pytest.mark.django_db
def test_load_search_client_expired_tokens_raises_exception(settings,
                                                            search_client):
    settings.SESSION_COOKIE_AGE = 9999999999
    user = mock_user('bob', ['search.api.globus.org'])
    user.last_login = timezone.now() - timedelta(days=3)
    user.save()
    with pytest.raises(ExpiredGlobusToken):
        load_search_client(user)


@pytest.mark.django_db
def test_load_search_client_with_bad_token(search_client):
    user = mock_user('bob', ['transfer.api.globus.org'])
    with pytest.raises(ValueError):
        load_search_client(user)


def test_load_transfer_client_with_anonymous_user(transfer_client):
    with pytest.raises(PortalAuthException):
        load_transfer_client(AnonymousUser())


@pytest.mark.django_db
def test_load_transfer_client_with_real_user(transfer_client):
    user = mock_user('bob', ['transfer.api.globus.org'])
    load_transfer_client(user)
    args, kwargs = transfer_client.call_args
    assert 'authorizer' in kwargs


@pytest.mark.django_db
def test_load_transfer_client_with_bad_token(transfer_client):
    user = mock_user('alice', ['search.api.globus.org'])
    with pytest.raises(ValueError):
        load_transfer_client(user)


@pytest.mark.django_db
def test_logout_revokes_tokens(mock_app):
    user = mock_user('alice', ['auth.globus.org', 'search.api.globus.org'
                               'transfer.api.globus.org'])
    revoke_globus_tokens(user)
    # Twice for each service access_token, and refresh_token
    assert mock_app.return_value.oauth2_revoke_token.call_count == 6


@pytest.mark.django_db
def test_revocation_globus_err(mock_app, globus_api_error):
    mock_app.return_value.oauth2_revoke_token.side_effect = globus_api_error

    user = mock_user('alice', ['auth.globus.org', 'search.api.globus.org'
                               'transfer.api.globus.org'])
    revoke_globus_tokens(user)
    assert mock_app.return_value.oauth2_revoke_token.call_count == 3


@pytest.mark.django_db
def test_get_groups_old_token_name(requests_get, user, client):
    # get user with public groups scope
    client.force_login(user)
    get_user_groups(user)
    assert user.is_authenticated is True
    assert requests_get.called
    assert requests_get.return_value.json.called


@pytest.mark.django_db
def test_get_groups_token_name(requests_get, user, client):
    # get user with public groups scope
    client.force_login(user)
    get_user_groups(user)
    assert user.is_authenticated is True
    assert requests_get.called
    assert requests_get.return_value.json.called


@pytest.mark.django_db
def test_get_groups_bad_token_name(requests_get, client):
    # get user with public groups scope
    user = mock_user('eda_the_owl_lady', ['groups.are.not.my.style'])
    client.force_login(user)
    with pytest.raises(ValueError):
        get_user_groups(user)


@pytest.mark.django_db
def test_get_groups_err_response(requests_get, user, client):
    # get user with public groups scope
    client.force_login(user)
    requests_get.return_value.raise_for_status.side_effect = \
        requests.HTTPError()
    with pytest.raises(GroupsException):
        get_user_groups(user)
