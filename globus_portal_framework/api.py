import logging
import requests
from django.http import StreamingHttpResponse
from django.core.exceptions import PermissionDenied
from django.core.exceptions import SuspiciousOperation
from .gclients import load_globus_access_token


log = logging.getLogger(__name__)


def restricted_endpoint_proxy_stream(request):
    if not request.user.is_authenticated:
        raise PermissionDenied
    url = request.GET.get('url')
    resource_server = request.GET.get('resource_server')
    if not url:
        raise SuspiciousOperation
    headers = {}
    if resource_server:
        try:
            token = load_globus_access_token(request.user, resource_server)
            headers['Authorization'] = 'Bearer {}'.format(token)
        except ValueError:
            raise SuspiciousOperation
    r = requests.get(url, headers=headers, stream=True)
    return StreamingHttpResponse(streaming_content=r)
