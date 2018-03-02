import globus_sdk


def load_globus_client(user, client, token_name):
    """Load a globus client with a given user and the name of the token. If
    the user is Anonymous (Not logged in), then an unauthenticated client is
    returned. If the client is logged in and the token is not found, a
    ValueError is raised.

    Example:
        >>> u = django.contrib.auth.models.User.objects.get(username='bob')
        >>> load_globus_client(u, globus_sdk.SearchClient, 'search.api.globus.org')  # noqa
    Given that bob is a logged in user, they will now have a search
    client capable of making searches on confidential data.
    Example2:
        >>> u = django.contrib.auth.models.AnonymousUser
        >>> load_globus_client(u, globus_sdk.SearchClient, 'search.api.globus.org')  # noqa
    An 'AnonymousUser' is not logged in, so they will get a regular search
    client and can only search on public data.
    """
    if user.is_authenticated:
        tok_list = user.social_auth.get(provider='globus').extra_data
        if tok_list.get('other_tokens'):
            service_tokens = {t['resource_server']: t
                              for t in tok_list['other_tokens']}
            service_token = service_tokens.get(token_name)
            if service_token:
                authorizer = globus_sdk.AccessTokenAuthorizer(
                    service_token['access_token'])
                return client(authorizer=authorizer)
            else:
                raise ValueError('Attempted to load {} for user {}, but no '
                                 'tokens existed with the name {}, only {}'
                                 ''.format(client, user, token_name,
                                           list(service_tokens.keys())))
    return client()
