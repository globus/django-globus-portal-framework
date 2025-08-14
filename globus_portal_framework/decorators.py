import typing as t
from functools import wraps
from urllib.parse import urlsplit, urlunsplit
import logging

from django.conf import settings
from django.http import QueryDict, HttpResponseRedirect
from globus_sdk.scopes import Scope
from globus_portal_framework.gclients import load_scopes
from globus_portal_framework.exc import ScopesRequired

log = logging.getLogger(__name__)


def scopes_required(scopes: t.List[Scope]):
    """
    Redirect the user to the login page, passing the given 'next' page.
    """
    login_url = settings.LOGIN_URL

    def decorator(view_func):
        # NOTE: This is likely obselete, and we can raise a ScopesRequired exception instead.
        def _redirect_to_login(request, *args, **kwargs):
            login_url_parts = list(urlsplit(login_url))
            querystring = QueryDict(login_url_parts[3], mutable=True)
            querystring["next"] = request.build_absolute_uri()
            querystring["scopes"] =  ' '.join([str(s) for s in scopes])
            login_url_parts[3] = querystring.urlencode(safe="/")
            url = urlunsplit(login_url_parts)
            log.debug(f"User login with url: {url}")
            return HttpResponseRedirect(url)

        def _view_wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                log.debug("User is not authenticated, logging them in again!")
                return _redirect_to_login(request)
            user_scopes = load_scopes(request.user)
            scopes_set, user_scopes_set = set(scopes), set(user_scopes)
            if not scopes_set.issubset(user_scopes_set):
                log.debug(f"User missing scope: {scopes_set.difference(user_scopes_set)}")
                return _redirect_to_login(request)
            log.debug(f"{request.user}: Scopes satisfied: {scopes}")
            return view_func(request, *args, **kwargs)
        return wraps(view_func)(_view_wrapper)
    return decorator
