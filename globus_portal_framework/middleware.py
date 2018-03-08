from django.http.response import HttpResponseRedirect
from globus_portal_framework.exc import TokenExpired
from django.utils.deprecation import MiddlewareMixin


class TokenExpiredMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        if not isinstance(exception, TokenExpired):
            return None
        return HttpResponseRedirect('/login/globus/?next=' + request.path)
