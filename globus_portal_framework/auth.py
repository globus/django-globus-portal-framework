"""
Globus Auth OpenID Connect backend, docs at:
    https://docs.globus.org/api/auth
"""
import logging
import typing as t
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

    def auth_allowed(self, response: t.Mapping[str, dict], details: t.Mapping[str, dict]) -> bool:
        """
        Overrided auth_allowed here:
        https://github.com/python-social-auth/social-core/blob/master/social_core/backends/base.py#L155

        Additionally checks for Globus Group access.
        """
        allowed = super(GlobusOpenIdConnect, self).auth_allowed(response, details)
        # Super currently checks manual whitelists. Ensure that check is still done,
        # and abort if the check fails.
        if not allowed:
            return allowed

        allowed_groups = self.setting('ALLOWED_GROUPS', [])
        if not allowed_groups:
            log.debug('settings.SOCIAL_AUTH_GLOBUS_ALLOWED_GROUPS is not '
                      'set, all users are allowed.')
            return allowed

        identity_id = response.get('sub')
        username = details.get('username')
        user_groups = self.get_user_globus_groups(response.get('other_tokens'))

        allowed_user_member_groups = self.match_identity_to_groups(identity_id, user_groups, allowed_groups)
        if allowed_user_member_groups:
            group_names = [f"{g['name']} ({g['id']})" for g in allowed_user_member_groups]
            groups_fmt = ", ".join(group_names)
            log.info(f"User {username} ({identity_id}) granted access via groups: {groups_fmt}")
            return True
        log.debug(f"User {username} ({identity_id}) denied access (not member of any configured group)")
        # Note: Typically this should return False, but instead it throws it's own AuthForbidden
        # exception, which can be handled elsewhere in middlewhere to redict to the groups page
        # where a user can login.
        raise AuthForbidden(
            self, {'allowed_user_member_groups': allowed_user_member_groups}
        )

    def match_identity_to_groups(self, identity_id: str, user_groups: t.List[t.Mapping[str, dict]], allowed_groups: t.List[t.Mapping[str, dict]]) -> t.List[t.Mapping[str, dict]]:
        """
        :param identity_id: The logged in users identity uuid (sub in OpenID)
        :param user_groups: All groups the identity_id is a member of
        :param allowed_groups: The configured groups where a user is allowed
        :returns: subset of allowed_groups where any user identity is a member
        """
        # Reduce groups to intersecting user_groups and portal defined allowed groups
        allowed_group_ids = [g['uuid'] for g in allowed_groups]
        intersecting_allowed_groups = [group for group in user_groups
                                       if group['id'] in allowed_group_ids]
        return intersecting_allowed_groups

    def get_user_globus_groups(self, other_tokens: t.Mapping[str, dict]):
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
        return groups_client.get_my_groups().data

    def auth_params(self, state=None):
        params = super(GlobusOpenIdConnect, self).auth_params(state)
        return params
