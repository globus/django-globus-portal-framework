from django.conf import settings


# Variables stored per-search entry on the Globus Search index.
__DEFAULT_ESVS = {
    'globus_group': 'globus_group',
    'globus_http_link': 'globus_http_link',
    'globus_http_scope': 'globus_http_scope',
    'remote_file_manifest': None
}
ENTRY_SERVICE_VARS_MAPPER = getattr(settings, 'ENTRY_SERVICE_VARS_MAPPER',
                                    ('globus_portal_framework',
                                     'default_service_vars_mapper'))
ENTRY_SERVICE_VARS = getattr(settings, 'ENTRY_SERVICE_VARS', __DEFAULT_ESVS)

# TODO: Deprecated -- Remove in 0.3.0
GLOBUS_HTTP_ENDPOINT = getattr(settings, 'GLOBUS_HTTP_ENDPOINT', '')
# TODO: Deprecated -- Remove in 0.3.0
PREVIEW_TOKEN_NAME = getattr(settings, 'PREVIEW_TOKEN_NAME', '<No Token Name'
                                                             'Set>')
PREVIEW_DATA_SIZE = getattr(settings, 'PREVIEW_DATA_SIZE', 2048)
