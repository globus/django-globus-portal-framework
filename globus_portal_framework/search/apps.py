"""
This app is no longer used. It exists simply to throw a warning during setup
to remove old references. It should be removed in version 0.4.0 or later.
"""
from django.apps import AppConfig


class GlobusPortalFrameworkSearchAppConfig(AppConfig):
    name = 'globus_portal_framework.search'
