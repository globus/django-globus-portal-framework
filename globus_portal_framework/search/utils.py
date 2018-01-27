import json
import globus_sdk

from django.conf import settings


def load_search_client(user):
    if user.is_authenticated:
        token = user.social_auth.get(provider='globus')\
            .extra_data['access_token']
        authorizer = globus_sdk.AccessTokenAuthorizer(token)
        return globus_sdk.SearchClient(authorizer=authorizer)
    return globus_sdk.SearchClient()


def map_to_datacite(search_data):
    with open(settings.SERACH_FORMAT_FILE) as f:
        raw_data = f.read()
        fields = json.loads(raw_data)

    detail_data = {}
    for name, data in fields.items():
        field_name = None
        if name in search_data.keys():
            field_name = name
        if not field_name:
            aliases = set(search_data.keys()) & set(data.get('aliases', []))
            if any(aliases):
                field_name = aliases.pop()
        if field_name:
            detail_data[name] = data.copy()
            detail_data[name]['value'] = search_data[field_name]

    return detail_data
