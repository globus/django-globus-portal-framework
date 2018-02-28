import requests


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
