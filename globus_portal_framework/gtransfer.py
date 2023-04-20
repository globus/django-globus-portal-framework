import requests
import globus_sdk
import logging
import os
from django.core.validators import URLValidator


from globus_portal_framework import (
    PreviewPermissionDenied, PreviewServerError, PreviewException,
    PreviewBinaryData, PreviewNotFound, ExpiredGlobusToken,

    load_transfer_client, load_globus_access_token, validate_token
)

log = logging.getLogger(__name__)


def check_exists(user, src_ep, src_path, raises=False):
    """Check if a file exists on a Globus Endpoint

    If the file exists, Returns True

    Raises globus_sdk.TransferAPIError if the file does not exist,
    the endpoint is not active, or the user does not have permission."""
    is_file(user, src_ep, src_path, raises=raises)
    return True


def is_file(user, src_ep, src_path, raises=False):
    """Check if a file exists on a Globus Endpoint

    Return true if the path at the endpoint is a file, false if it's a
    directory, and false if the file does not exist.

    :param raises: Raise a TransferAPIError if the file/dir does not exist

    Raises globus_sdk.TransferAPIError if the file does not exist,
    the endpoint is not active, or the user does not have permission."""
    tc = load_transfer_client(user)
    try:
        tc.operation_ls(src_ep, path=src_path)
        return False
    except globus_sdk.TransferAPIError as tapie:
        # File exists but is not a directory. We'll not take it personally.
        if tapie.code == 'ExternalError.DirListingFailed.NotDirectory':
            return True
        elif not raises:
            return False
        else:
            raise


def get_helper_page_url(callback_url, cancel_url='', folder_limit=5,
                        file_limit=5, label=''):
    """
    Get a link for the Globus helper page

    https://docs.globus.org/api/helper-pages/browse-endpoint/

    Raises ValidationError if callback_url or cancel_url is malformed
    :param callback_url: The URL the user will be redirected to after choosing
    files and folders on the Globus helper page. You should define a POST
    endpoint and use the django.views.decorators.csrf.csrf_exempt decorator
    :param cancel_url: The panic 'nope' url. You should use the same URL you
    used to show this link, which you can get with request.build_absolute_uri()
    :param folder_limit: folders the user can choose, or 0 if they can't
    :param file_limit: files the user can choose, or 0 if they can't
    :param label: Label for transfer, showing up on the globus.org status page
    :return: A URL for the browse endpoint helper page
    """
    check_url_valid = URLValidator()
    check_url_valid(callback_url)
    params = {
            'method': 'POST',
            'action': callback_url,
            'folderlimit': folder_limit,
            'filelimit': file_limit,
            'label': label or 'Service Transfer Request'
        }
    if cancel_url:
        check_url_valid(cancel_url)
        params['cancelurl'] = cancel_url
    return requests.Request(
        'GET',
        'https://app.globus.org/file-manager',
        params=params
    ).prepare().url


def helper_page_transfer(request, endpoint, path, helper_page_is_dest=True):
    """Transfer the result of a helper page to a given endpoint and path.

    NOTE! Currently only transferring a file to a folder is supported.

    :param request: The request, for gleaning POST data and error checking
    :param ep: Globus endpoint for transfer
    :param path: path for the 'ep' globus endpoint
    :param helper_page_is_dest: designate if the endpoint and path from the
    helper page should be used for the destination on this transfer.
    If not, it will be the source.
    :return: A TranferData object for a Globus transfer
    http://globus-sdk-python.readthedocs.io/en/stable/clients/transfer/#globus_sdk.TransferData  # noqa
    """
    if request.method != 'POST':
        raise ValueError('Helper Page Transfer must be done in a POST request')
    if request.user.is_anonymous:
        raise ValueError('User must be logged in to transfer data.')
    if request.POST.get('folder[1]') or request.POST.get('file[0]'):
        raise NotImplementedError('Only zero or one folder is supported.')

    h_ep, h_path = request.POST.get('endpoint_id'), request.POST.get('path')
    os.path.join(h_path, request.POST.get('folder[0]', ''))

    if helper_page_is_dest:
        src_ep, src_path, dest_ep, dest_path = endpoint, path, h_ep, h_path
    else:
        src_ep, src_path, dest_ep, dest_path = h_ep, h_path, endpoint, path

    return transfer_file(request.user, src_ep, src_path, dest_ep,
                         dest_path, request.POST.get('label'))


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


def preview(user, url, scope, chunk_size=512):
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
        token = load_globus_access_token(user, scope)
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
                    raise ExpiredGlobusToken(token_name=scope)
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
