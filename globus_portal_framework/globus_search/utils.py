import globus_sdk


def load_search_client(user):
    if user.is_authenticated:
        token = user.social_auth.get(provider='globus')\
            .extra_data['access_token']
        authorizer = globus_sdk.AccessTokenAuthorizer(token)
        return globus_sdk.SearchClient(authorizer=authorizer)
    return globus_sdk.SearchClient()
