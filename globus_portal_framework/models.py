import logging
from django.db import models
from django.contrib.auth.models import Group
from django.conf import settings

import globus_sdk

from globus_portal_framework.gclients import (
    load_globus_confidential_client,
    load_search_client
)

log = logging.getLogger(__name__)


class SearchAuthProxy(models.Model):
    """
    """
    client = models.UUIDField(help_text='Globus App credentials used in the '
                                        'search')
    group = models.ForeignKey(Group, on_delete=models.CASCADE,
                              help_text='The Group these searches should apply'
                              )

    class Meta:
        verbose_name_plural = 'SearchAuthProxies'

    def __str__(self):
        for cid, client_name in self.get_clients():
            if cid == str(self.client):
                return client_name
        log.warning('Saved DB Object SearchAuthProxy client "{}" has no '
                    'corresponding entry in settings.CONFIDENTIAL_CLIENTS'
                    ''.format(self.client)
                    )
        return '<Unknown Client>'

    @classmethod
    def get_client_for_user(cls, user):
        proxies = cls.objects.filter(group__in=user.groups.all())
        if len(proxies) > 1:
            log.warning('Multiple proxies for user {}: {}. You should remove '
                        'one of these.'.format(user, proxies))
        proxy = proxies.first()
        log.debug('Proxy for user {}: {}'.format(user, proxy or None))
        if proxy:
            scopes = ('urn:globus:auth:scope:search.api.globus.org:search',)
            cc_authorizer = globus_sdk.ClientCredentialsAuthorizer(
                load_globus_confidential_client(str(proxy.client)),
                scopes
            )
            return globus_sdk.SearchClient(authorizer=cc_authorizer)
        return load_search_client(user)

    @staticmethod
    def get_clients():
        choices = [(c['client_id'], c['name'])
                   for c in getattr(settings, 'CONFIDENTIAL_CLIENTS', {})]
        cids = [c[0] for c in choices]
        if settings.SOCIAL_AUTH_GLOBUS_KEY not in cids:
            choices.append((settings.SOCIAL_AUTH_GLOBUS_KEY,
                           'Main Portal'))
        return choices
