from django.contrib.auth.models import User
from social_django.models import UserSocialAuth
import globus_sdk


class MockGlobusClient:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


def mock_user(username, tokens):
    """
    Give a username and tokens and this will mock out python_social_auth
    with the given globus tokens.
    :param username: Any string, such as 'bob' or 'joe@globusid.org'
    :param tokens: token scopes, such as ['search.api.globus.org']
    :return: Django User Object
    """
    user = User.objects.create_user(username=username)
    extra_data = {
        'user': user,
        'provider': 'globus',
        'extra_data': {'other_tokens': [
            {'resource_server': token,
             'access_token': 'foo'}
        ] for token in tokens}
    }
    soc_auth = UserSocialAuth.objects.create(**extra_data)
    user.provider = 'globus'
    user.save()
    soc_auth.save()
    return user


def globus_client_is_loaded_with_authorizer(client):
    return isinstance(client.kwargs.get('authorizer'),
                      globus_sdk.AccessTokenAuthorizer)
