from django.conf import settings


GLOBUS_HTTP_ENDPOINT = getattr(settings, 'GLOBUS_HTTP_ENDPOINT', '')
