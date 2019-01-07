import logging
from urllib.parse import urlencode
from django.http.response import HttpResponseRedirect
from django.utils.deprecation import MiddlewareMixin
from django.urls import reverse
from django.contrib import auth

from globus_portal_framework.exc import ExpiredGlobusToken

log = logging.getLogger(__name__)


class ExpiredTokenMiddleware(MiddlewareMixin):
    """
    Catch the globus_portal_framework.ExpiredGlobusToken exception and
    redirect them to the login page with the redirection link set to
    the path they were originally going to. Most times, the user will already
    be logged into Globus, and so this will manifest as a request that takes
    slightly longer than usual, as it does all the OAuth redirects to grab
    tokens then does the work the user originally intended.
    """

    PROVIDER = 'globus'

    def process_exception(self, request, exception):
        if isinstance(exception, ExpiredGlobusToken):
            log.info('Tokens expired for user {}, redirecting to login.'
                     ''.format(request.user))
            auth.logout(request)
            # build /login/globus/?next=/my-intended-url/'
            url = '{}{}/?{}'.format(reverse('login'),
                                    self.PROVIDER,
                                    urlencode({'next': request.path}))
            return HttpResponseRedirect(url)
