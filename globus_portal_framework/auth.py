"""
Globus Auth OpenID Connect backend, docs at:
    https://docs.globus.org/api/auth
"""

from social_core.backends.globus import GlobusOpenIdConnect as GlobusOpenIdConnectBase
from social_core.exceptions import AuthForbidden


class GlobusOpenIdConnect(GlobusOpenIdConnectBase):
    NEXUS_ENDPOINT = 'https://nexus.api.globusonline.org'
    NEXUS_SCOPE = 'urn:globus:auth:scope:nexus.api.globus.org:groups'
    GLOBUS_APP_URL = 'https://app.globus.org'

    def get_user_details(self, response):
        # If SOCIAL_AUTH_GLOBUS_SESSIONS is not set, fall back to default
        if not self.setting('SESSIONS'):
            return super(GlobusOpenIdConnectBase, self).get_user_details(response)

        key, secret = self.get_key_and_secret()
        auth_token = response.get('access_token')

        # Introspect the access_token with session_info and identities_set included
        resp = self.get_json(
            self.OIDC_ENDPOINT + '/v2/oauth2/token/introspect',
            method='POST',
            data={"token": auth_token, "include": "session_info,identities_set"},
            auth=(key, secret)
        )

        # Get all user identities
        identities_set = resp.get('identities_set')

        # Find the latest authentication
        ids = resp.get('session_info').get('authentications').items()
        identity_id = None
        idp_id = None
        auth_time = 0
        for auth_key, auth_info in ids:
            at = auth_info.get('auth_time')
            if at > auth_time:
                identity_id = auth_key
                idp_id = auth_info.get('idp')
                auth_time = at

        # Get user identities
        resp = self.get_json(
            self.OIDC_ENDPOINT + '/v2/api/identities',
            method='GET',
            headers={'Authorization': 'Bearer ' + auth_token},
            params={'ids': ','.join(identities_set),
                    'include': 'identity_provider'},
        )

        for item in resp.get('identities'):
            if item.get('id') == identity_id:
                fullname, first_name, last_name = self.get_user_names(
                    item.get('name'))
                return {
                    'username': item.get('username'),
                    'email': item.get('email'),
                    'fullname': fullname,
                    'first_name': first_name,
                    'last_name': last_name,
                    'identity_id': identity_id,
                    'idp_id': idp_id,
                    'identities': resp
                }

        return None

    def get_user_id(self, details, response):
        if not self.setting('SESSIONS'):
            return super(GlobusOpenIdConnect, self).get_user_id(details, response)
        return details.get('idp_id') + '_' + details.get('identity_id')

    def auth_allowed(self, response, details):
        if not self.setting('SESSIONS'):
            return super(GlobusOpenIdConnect, self).auth_allowed(response, details)

        allowed_group = self.setting('ALLOWED_GROUP')
        if not allowed_group:
            return True

        identity_id = details.get('identity_id')

        # Get a nexus access token
        other_tokens = response.get('other_tokens')
        nexus_token = None
        for item in other_tokens:
            if item.get('scope') == self.NEXUS_SCOPE:
                nexus_token = item.get('access_token')

        # Get the allowed group
        resp = self.get_json(
            self.NEXUS_ENDPOINT + '/groups/' + allowed_group,
            method='GET',
            headers={'Authorization': 'Bearer ' + nexus_token}
        )
        identity_set_properties = resp.get('identity_set_properties')
        group_name = resp.get('name')
        group_join_url = self.GLOBUS_APP_URL + resp.get('join').get('url')

        # Check if group membership status for the identity_id is active
        identity_property = identity_set_properties.get(identity_id)
        if identity_property.get('status') == 'active':
            return True

        # Find first identity id with active group membership status
        for identity_id, identity_property in identity_set_properties.items():
            if identity_property.get('status') == 'active':
                raise AuthForbidden(
                    self,
                    {'group_name': group_name,
                     'session_required_identities': identity_id}
                )

        # If none of the user identity ids is a member of the group, propose to join the group
        raise AuthForbidden(
            self, {'group_name': group_name, 'group_join_url': group_join_url})

    def auth_params(self, state=None):
        params = super(GlobusOpenIdConnect, self).auth_params(state)

        # If Globus sessions are enabled, force Globus login, and specify a required identity if already known
        if not self.setting('SESSIONS'):
            return params
        params['prompt'] = 'login'
        session_message = self.strategy.session_pop('session_message')
        if session_message:
            params['session_message'] = session_message
            params['session_required_identities'] = self.strategy.session_pop(
                'session_required_identities')
        return params
