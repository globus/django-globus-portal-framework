from datetime import datetime
import pytz
from django.contrib.auth.models import User
from django.test import Client
from django.urls import path, include
from social_django.models import UserSocialAuth
from globus_portal_framework.urls import register_custom_index
import globus_sdk

from globus_portal_framework.views import logout

# Two days in seconds
TOKEN_EXPIRE_TIME = 48 * 60 * 60

MOCK_EMPTY_SEARCH = {
    "@datatype": "GSearchResult",
    "@version": "2017-09-01",
    "count": 0,
    "gmeta": [],
    "offset": 0,
    "total": 0
}


class MockGlobusClient:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class MockTransferAPIError(Exception):
    """Mock Globus exception"""
    def __init__(self, code='', message=''):
        self.code = code
        self.message = message


class MockTransferClient(MockGlobusClient):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.raise_on_ls = kwargs.get('raise_on_ls', False)
        self.exc_code = kwargs.get('exc_code', 'ExternalError.'
                                               'DirListingFailed.NotDirectory')
        self.exc_mess = kwargs.get('message', '')

    def operation_ls(self, *args, **kwargs):
        if self.raise_on_ls:
            exc = globus_sdk.TransferAPIError()
            exc.code = self.exc_code
            exc.message = self.exc_mess
            raise exc


def mock_tokens(resource_servers):
    return [
        {
            'resource_server': token,
            'access_token': 'access_token',
            'refresh_token': 'refresh_token',
            'expires_in': TOKEN_EXPIRE_TIME
        } for token in resource_servers
    ]


def mock_user(username, resource_servers):
    """
    Give a username and tokens and this will mock out python_social_auth
    with the given globus tokens.
    :param username: Any string, such as 'bob' or 'joe@globusid.org'
    :param tokens: token scopes, such as ['search.api.globus.org']
    :return: Django User Object
    """
    user = User.objects.create_user(username, username + '@globus.org',
                                    'globusrocks')
    extra_data = {
        'user': user,
        'provider': 'globus',
        'extra_data': {
            'other_tokens': mock_tokens(resource_servers),
            'access_token': 'auth_access_token',
            'refresh_token': 'auth_refresh_token'
        }
    }
    user.last_login = datetime.now(pytz.utc)
    soc_auth = UserSocialAuth.objects.create(**extra_data)
    user.provider = 'globus'
    user.save()
    soc_auth.save()
    return user


def get_logged_in_client(username, tokens):
    c = Client()
    user = mock_user(username, tokens)
    # Password is set in mocks, and is always 'globusrocks' for this func
    c.login(username=username, password='globusrocks')
    return c, user


def globus_client_is_loaded_with_authorizer(client):
    return isinstance(client.kwargs.get('authorizer'),
                      globus_sdk.AccessTokenAuthorizer)


def rebuild_index_urlpatterns(old_urlpatterns, indices):
    """
    This fixes pre-complied paths not matching new test paths. Since paths
    are compiled at import time, if you override settings with new
    SEARCH_INDEXES, your new search indexes won't have urls that match due to
    the regexes already being compiled. The problem stems from the UrlConverter
    containing explicit names of the SEARCH_INDEXES which don't handle change
    well. Use this function to rebuild the names to pick up on your test index
    names.
    :param old_urlpatterns: patterns you want to rebuild
    :param indices: The list of new search indices you're using
        Example: ['mytestindex', 'myothertestindex']
    :return: urlpatterns
    """
    urlpatterns = [
        path('logout/', logout, name='logout'),
        path('', include('social_django.urls', namespace='social')),
        # FIXME Remove after merging #55 python-social-auth-upgrade
        path('', include('django.contrib.auth.urls'))
    ]

    register_custom_index('custom_index', indices)

    for url in old_urlpatterns:
        if '<index:index>' in str(url.pattern):
            new_pattern = str(url.pattern).split('/')
            new_pattern[0] = '<custom_index:index>'
            new_pattern = '/'.join(new_pattern)
            urlpatterns.append(path(new_pattern, url.callback, name=url.name))
        else:
            urlpatterns.append(url)

    return urlpatterns
