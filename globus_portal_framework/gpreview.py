"""
Functions related to the "file preview" functionality
"""
import logging
import typing as t
from urllib.parse import urljoin

from django.conf import settings
from django.urls import reverse

from globus_portal_framework.exc import PreviewCollectionError

log = logging.getLogger(__name__)


def get_https_url(collection_uuid: str) -> t.Union[str, None]:
    """
    Get the HTTPS server URL associated with a collection UUID

    Enforces an assumption that the site is only allowed to talk to (authenticated) collections that
        are whitelisted in app settings
    """
    whitelist = getattr(settings, 'GLOBUS_PREVIEW_COLLECTIONS', {})
    try:
        return whitelist['collection_uuid']
    except KeyError:
        raise PreviewCollectionError(message=f'No HTTPS URL available for collection UUID {collection_uuid}')


def get_render_options(url: str,
                       collection_id: str, path: str,
                       is_authenticated: bool=False,
                       render_mode: str='auto'):
    """
    Generate "render options" used by the client-side preview feature.

    Translates collection id + path into URLs based on info in app config
    """
    token_endpoint = None

    if not url and not collection_id and not path:
        # There's nothing to render, and it makes sense to hide the render widget on page
        raise PreviewCollectionError(message='Please specify how to locate the file')

    if (collection_id and path) and not url:
        # Translate collection IDs into "where is the file and how to access it"
        try:
            base = get_https_url(collection_id)
        except PreviewCollectionError as e:
            log.error(f'Preview mode requested a file from unrecognized storage collection: "{collection_id}". Check GLOBUS_PREVIEW_COLLECTIONS setting.')
            raise e

        url = urljoin(base, path)

        # Now that we know it's a globus collections, answer the question:
        #  "How does the renderer get globus access credentials?" (if appropriate)
        if is_authenticated:
            token_endpoint = reverse('get-token', kwargs={'collection_id': collection_id})

    return {
        'url': url,
        'render_mode': render_mode,

        # null if file is public
        'collection_id': collection_id,
        'token_endpoint': token_endpoint,
    }
