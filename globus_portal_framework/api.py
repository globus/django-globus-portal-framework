import logging
import requests
import globus_sdk
import uuid
from django.http import StreamingHttpResponse, JsonResponse
from django.core.exceptions import PermissionDenied
from django.core.exceptions import SuspiciousOperation
from .gclients import load_globus_access_token, load_transfer_client


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


def operation_ls(request):
    tc = load_transfer_client(request.user)
    try:
        collection = uuid.UUID(request.GET['collection'])
        r = tc.operation_ls(str(collection), path=request.GET.get('path'))
        return JsonResponse(r.data)
    except ValueError:
        return JsonResponse({'message': '"collection" must be a UUID'},
                            status=400)
    except globus_sdk.services.transfer.errors.TransferAPIError as tapie:
        return JsonResponse(tapie.raw_json, status=tapie.http_status)
    except Exception:
        log.error('Encountered error on operation_ls API!', exc_info=True)
        return JsonResponse({'message': 'Unexpected Error, this is a bug!'},
                            status=500)
