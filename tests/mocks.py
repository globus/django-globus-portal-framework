from datetime import datetime
import pytz
import pathlib
import uuid
from django.contrib.auth.models import User
from social_django.models import UserSocialAuth
import globus_sdk

import json

mocks_path = pathlib.Path(__file__).parent / 'data'
mock_data = {}
for mpath in mocks_path.iterdir():
    with open(mpath) as f:
        print(f'FETCHING {mpath.stem}')
        mock_data[mpath.stem] = json.loads(f.read())


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


class MockGlobusAPIError(Exception):
    """Mock Globus exception"""
    def __init__(self, code='', message='', http_status=400):
        self.code = code
        self.message = message
        self.http_status = 400


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
        'uid': str(uuid.uuid4()),
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
