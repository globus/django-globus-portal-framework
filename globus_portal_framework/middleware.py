from django.http.response import HttpResponseRedirect
from globus_portal_framework.exc import ExpiredGlobusToken
from django.utils.deprecation import MiddlewareMixin


class ExpiredTokenMiddleware(MiddlewareMixin):
    """
    Catch the globus_portal_framework.ExpiredGlobusToken exception and
    redirect them to the login page with the redirection link set to
    the path they were originally going to. Most times, the user will already
    be logged into Globus, and so this will manifest as a request that takes
    slightly longer than usual, as it does all the OAuth redirects to grab
    tokens then does the work the user originally intended.
    """

    REDIRECT_TEMPLATE = '/login/globus/?next={}'

    def process_exception(self, request, exception):
        if isinstance(exception, ExpiredGlobusToken):
            return HttpResponseRedirect(self.REDIRECT_TEMPLATE.format(
                                        request.path))
