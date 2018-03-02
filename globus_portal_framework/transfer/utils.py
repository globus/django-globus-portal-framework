import requests
import globus_sdk
import logging
import os

from globus_portal_framework.utils import load_globus_client

log = logging.getLogger(__name__)


def load_transfer_client(user):
    return load_globus_client(user, globus_sdk.TransferClient,
                              'transfer.api.globus.org')


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
    if len(url_chunks) >= 2 and len(url_chunks[0]) == 36:
        return {
            'endpoint': url_chunks[0],
            # Not actually sure if extra ':' are valid, but we'll reconstruct
            # the URL accordingly just to be sure.
            'path': ':'.join(url_chunks[1:])
        }
    raise ValueError('Unable to find ":" to split path from endpoint for {}'
                     ''.format(url))


def preview(url, chunk_size=512):
    """Download the first number of 'bytes' the given 'url'

    Raises ValueError if the url produced a connection error
    """
    # Use 'with' with 'stream' so we close the connection after we
    # return.
    try:
        with requests.get(url, stream=True) as r:
            if r.status_code is not 200:
                raise ValueError('Request returned non-ok code: ' +
                                 r.status_code)
            return next(r.iter_content(chunk_size=chunk_size)).decode('utf-8')
    except requests.exception.ConnectionError:
        raise ValueError('Connection Error in request')
