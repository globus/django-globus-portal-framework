from datetime import datetime
import pytz
from django.contrib.auth.models import User
from django.test import Client
from social_django.models import UserSocialAuth
import globus_sdk

# Two days in seconds
TOKEN_EXPIRE_TIME = 48 * 60 * 60


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


def mock_user(username, tokens):
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
        'extra_data': {'other_tokens': [
            {'resource_server': token,
             'access_token': 'foo', 'expires_in': TOKEN_EXPIRE_TIME}
            for token in tokens]
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
