import requests
import globus_sdk
import logging
import os

from globus_portal_framework.utils import (load_globus_client,
                                           load_globus_access_token,
                                           validate_token)
from globus_portal_framework import (PreviewPermissionDenied,
                                     PreviewServerError, PreviewException,
                                     PreviewBinaryData, PreviewNotFound,
                                     ExpiredGlobusToken)
from globus_portal_framework.transfer import settings as transfer_settings

log = logging.getLogger(__name__)


def load_transfer_client(user):
    return load_globus_client(user, globus_sdk.TransferClient,
                              'transfer.api.globus.org')


def check_exists(user, src_ep, src_path):
    """Check if a file exists on a Globus Endpoint

    If the file exists, Returns True

    Raises globus_sdk.TransferAPIError if the file does not exist,
    the endpoint is not active, or the user does not have permission."""
    tc = load_transfer_client(user)
    try:
        tc.operation_ls(src_ep, path=src_path)
    except globus_sdk.TransferAPIError as tapie:
        # File exists but is not a directory. We'll not take it personally.
        if tapie.code == 'ExternalError.DirListingFailed.NotDirectory':
            pass
        else:
            raise
    return True


def transfer_file(user, source_endpoint, source_path,
                  dest_endpoint, dest_path, label):
    """

    :param user: Must be a Django user with permissions to initiate the
    transfer
    :param source_endpoint: Source Endpoint UUID
    :param source_path: Source path, including the filename
    :param dest_endpoint: Destination Endpoint UUID
    :param dest_path: Destination path, including the filename
    :param label: Label to use for the transfer
    :return: A globus SDK task object.
    """
    log.debug('transferring {}:{} to {}'.format(source_endpoint, source_path,
                                                dest_endpoint))
    tc = load_transfer_client(user)
    tdata = globus_sdk.TransferData(tc, source_endpoint, dest_endpoint,
                                    label=label, sync_level="checksum")
    tdata.add_item(source_path,
                   os.path.join(dest_path, os.path.basename(source_path))
                   )
    return tc.submit_transfer(tdata)


def parse_globus_url(url):
    """Parse a Globus URL string of the format:
        globus://<UUID Endpoint>:<Path>
        globus://ddb59aef-6d04-11e5-ba46-22000b92c6ec:/share/godata/file1.txt

        returns a dict of the format:
        {
            'endpoint': 'ddb59aef-6d04-11e5-ba46-22000b92c6ec'
            'path': '/share/godata/file1.txt'
        }

        Raises ValueError if invalid format
    """
    if 'globus://' not in url:
        raise ValueError('url "{}" did not start with "globus://"'.format(url))
    url_chunks = url.replace('globus://', '').split(':')
    if len(url_chunks) < 2:
        raise ValueError('Unable to find ":" to split path from endpoint for '
                         '{}'.format(url))
    if len(url_chunks[0]) != 36:
        raise ValueError('Malformed Globus endpoint UUID does not'
                         'contain 36 characters: {}'
                         ''.format(url_chunks[0]))
    return url_chunks[0], ':'.join(url_chunks[1:])


def preview(user, url, chunk_size=512):
    """Download the first number of 'bytes' the given 'url'

    Raises PreviewException if fetching the preview data if there are any
    errors, which will be one of the following Exceptions:
    (All exceptions located under globus_portal_framework)
    * PreviewPermissionDenied -- insufficient permissions
    * PreviewNotFound -- file not found on preview server
    * PreviewBinaryData -- Data is not text
    * PreviewServerError -- Preview server threw a 500 error
    * PreviewException -- Something else we didn't expect
    """
    try:
        token = load_globus_access_token(user,
                                         transfer_settings.PREVIEW_TOKEN_NAME)
        headers = {'Authorization': 'Bearer {}'.format(token)}
        # Use 'with' with 'stream' so we close the connection after we return.
        with requests.get(url, stream=True, headers=headers) as r:
            if r.status_code == 200:
                chunk = next(r.iter_content(chunk_size=chunk_size)).decode(
                             'utf-8')
                # The last line will likely come back truncated, so chop it off
                # so that the preview data we get is cleaner. Since all the
                # data we get back will be text (we can't process other
                # formats), this should always work.
                return '\n'.join(chunk.split('\n')[:-1])
            elif r.status_code == 401:
                if not validate_token(token):
                    raise ExpiredGlobusToken(
                        token_name=transfer_settings.PREVIEW_TOKEN_NAME)
                raise PreviewPermissionDenied()
            elif r.status_code == 403:
                raise PreviewPermissionDenied()
            elif r.status_code == 404:
                raise PreviewNotFound()
            elif r.status_code >= 500 or r.status_code < 600:
                raise PreviewServerError(r.status_code, r.text)
            else:
                raise PreviewException()
    except UnicodeDecodeError:
        raise PreviewBinaryData()
