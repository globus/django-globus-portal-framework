"""
Globus Auth OpenID Connect backend, docs at:
    https://docs.globus.org/api/auth
"""
import logging
import urllib
from social_core.backends.globus import (
    GlobusOpenIdConnect as GlobusOpenIdConnectBase
)
from social_core.exceptions import AuthForbidden
import globus_sdk
from globus_sdk.scopes import GroupsScopes
from globus_sdk import config as globus_sdk_config

log = logging.getLogger(__name__)


class GlobusOpenIdConnect(GlobusOpenIdConnectBase):

    OIDC_ENDPOINT = globus_sdk_config.get_service_url('auth')
    GLOBUS_APP_URL = 'https://app.globus.org'
    # Fixed by https://github.com/python-social-auth/social-core/pull/577
    JWT_ALGORITHMS = ['RS512']

    def introspect_token(self, auth_token):
        url = urllib.parse.urljoin(self.OIDC_ENDPOINT,
                                   'v2/oauth2/token/introspect')
        return self.get_json(
            url,
            method='POST',
            data={"token": auth_token,
                  "include": "session_info,identities_set"},
            auth=self.get_key_and_secret()
        )

    def get_globus_identities(self, auth_token, identities_set):
        url = urllib.parse.urljoin(self.OIDC_ENDPOINT,
                                   '/v2/api/identities')
        return self.get_json(
            url,
            method='GET',
            headers={'Authorization': 'Bearer ' + auth_token},
            params={'ids': ','.join(identities_set),
                    'include': 'identity_provider'},
        )

    def get_user_details(self, response):
        # If SOCIAL_AUTH_GLOBUS_SESSIONS is not set, fall back to default
        if not self.setting('SESSIONS'):
            return super(GlobusOpenIdConnectBase, self).get_user_details(
                response)

        auth_token = response.get('access_token')
        introspection = self.introspect_token(auth_token)
        identities_set = introspection.get('identities_set')

        # Find the latest authentication
        ids = introspection.get('session_info').get('authentications').items()

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
        user_identities = self.get_globus_identities(auth_token, identities_set)
        for item in user_identities.get('identities'):
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
                    'identities': user_identities
                }

        return None

    def get_user_id(self, details, response):
        if not self.setting('SESSIONS'):
            return super(GlobusOpenIdConnect, self).get_user_id(details,
                                                                response)
        return details.get('idp_id') + '_' + details.get('identity_id')

    def auth_allowed(self, response, details):
        if not self.setting('SESSIONS'):
            return super(GlobusOpenIdConnect, self).auth_allowed(response,
                                                                 details)

        allowed_groups = [g['uuid']
                          for g in self.setting('ALLOWED_GROUPS', [])]
        if not allowed_groups:
            log.info('settings.SOCIAL_AUTH_GLOBUS_ALLOWED_GROUPS is not '
                     'set, all users are allowed.')
            return True

        identity_id = details.get('identity_id')
        username = details.get('username')
        user_groups = self.get_user_globus_groups(response.get('other_tokens'))
        # Fetch all groups where the user is a member.
        allowed_user_groups = [group for group in user_groups
                               if group['id'] in allowed_groups]
        allowed_user_member_groups = []
        for group in allowed_user_groups:
            gname, gid = group.get('name'), group['id']
            for membership in group['my_memberships']:
                if identity_id == membership['identity_id']:
                    log.info('User {} ({}) granted access via group {} ({})'
                             .format(username, identity_id, gname, gid))
                    return True
                else:
                    allowed_user_member_groups.append(membership)
        log.debug('User {} ({}) is not a member of any allowed groups. '
                  'However, they may be able to login with {}'.format(
                      username, identity_id, allowed_user_member_groups)
                  )
        raise AuthForbidden(
            self, {'allowed_user_member_groups': allowed_user_member_groups}
        )

    def get_user_globus_groups(self, other_tokens):
        """
        Given the 'other_tokens' key provided by user details, fetch all
        groups a user belongs. The API is PUBLIC, and no special allowlists
        are needed to use it.
        """
        groups_scopes = (GroupsScopes.all,
                         GroupsScopes.view_my_groups_and_memberships)
        groups_token = None
        for item in other_tokens:
            if item.get('scope') in groups_scopes:
                groups_token = item.get('access_token')

        if groups_token is None:
            raise ValueError(
                f'You must set one of {groups_scopes} scopes on '
                'settings.SOCIAL_AUTH_GLOBUS_SCOPE in order to set an allowed'
            )

        authorizer = globus_sdk.AccessTokenAuthorizer(groups_token)
        groups_client = globus_sdk.GroupsClient(authorizer=authorizer)
        return groups_client.get_user_groups()

    def auth_params(self, state=None):
        params = super(GlobusOpenIdConnect, self).auth_params(state)

        # If Globus sessions are enabled, force Globus login, and specify a
        # required identity if already known
        if not self.setting('SESSIONS'):
            return params
        params['prompt'] = 'login'
        session_message = self.strategy.session_pop('session_message')
        if session_message:
            params['session_message'] = session_message
            params['session_required_identities'] = self.strategy.session_pop(
                'session_required_identities')
        return params
