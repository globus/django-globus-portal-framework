import globus_sdk


def load_search_client(access_token=None):
    # TODO: Support auth searches
    # authorizer = globus_sdk.AccessTokenAuthorizer(access_token) \
    #     if access_token else None
    return globus_sdk.SearchClient()
