from django.conf import settings


GLOBUS_HTTP_ENDPOINT = getattr(settings, 'GLOBUS_HTTP_ENDPOINT', '')
PREVIEW_TOKEN_NAME = getattr(settings, 'PREVIEW_TOKEN_NAME', '')
