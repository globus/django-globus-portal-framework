

class GlobusPortalException(Exception):
    def __init__(self, code='', message='', index=''):
        """
        :param code: A short string that can be checked against, such as
            'PermissionDenied'
        :param message: A longer string that describes the problem and action
            that should be taken.
        """
        self.code = code or 'UnexpectedError'
        self.message = message or (
            'Globus Portal Framework encountered an unexpected error'
        )
        self.index = index or '<Index Not Listed>'

    def __str__(self):
        return '{} on {}: {}'.format(self.code, self.index, self.message)

    def __repr__(self):
        return str(self)


class PortalAuthException(GlobusPortalException):
    def __init__(self, code='', message=''):
        self.code = code or 'PortalAuthException'
        self.message = message or 'The portal encountered an ' \
                                  'error authorizing this action'
        self.index = ''


class NonGlobusUserException(Exception):
    """A Django user does not a have an association with Globus in the
    social_django.models.UserSocialAuth Python Social Auth models.
    This exception is raised when an attempt at accessing a Globus Client
    for an authenticated Django user and GLOBUS_NON_USERS_ALLOWED_PUBLIC_ACCESS
    is False.
    """
    def __init__(self, code='', message=''):
        self.code = code or 'NonGlobusUserException'
        self.message = (
            message or 'Django user does not have a Globus User'
            'association in social_django.models.UserSocialAuth.'
        )
        self.index = ''


class GroupsException(GlobusPortalException):
    def __init__(self, code='', message=''):
        self.code = code or 'GroupsException'
        self.message = message or 'User Globus Groups could not be fetched'
        self.index = 'Index Not Applicable'


class IndexNotFound(GlobusPortalException):
    """
    Exception when user tried to access an index not defined by this portal
    """
    def __init__(self, index, **kwargs):
        super().__init__(**kwargs)
        self.code = 'IndexNotFound'
        self.index = index
        self.message = ('The index "{}" was not defined for this portal'
                        ''.format(index)
                        )


class PreviewException(GlobusPortalException):
    """
    Exceptions when trying to fetch data from Globus Preview
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.code = 'UnexpectedError'
        self.message = 'There was an unexpected error ' \
                       'when fetching preview data.'


class PreviewPermissionDenied(PreviewException):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.code = 'PermissionDenied'
        self.message = 'You do not have access to view this data'


class PreviewURLNotFound(PreviewException):
    def __init__(self, subject, **kwargs):
        super().__init__(**kwargs)
        self.code = 'URLNotFound'
        self.message = 'No Globus HTTP URL was provided for this search ' \
                       'entry'
        self.subject = subject


class PreviewNotFound(PreviewException):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.code = 'NotFound'
        self.message = 'Could not find file on the preview server'


class PreviewServerError(PreviewException):
    def __init__(self, http_code, server_error, **kwargs):
        super().__init__(**kwargs)
        self.code = 'ServerError'
        self.message = 'There was a problem with the Preview Server'
        self.http_code = http_code
        self.server_error = server_error

    def __str__(self):
        return '{}\nHttpCode: {}\nServer Text: {}'.format(super().__str__(),
                                                          self.http_code,
                                                          self.server_error)


class PreviewBinaryData(PreviewException):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.code = 'BinaryData'
        self.message = 'Preview is unable to display binary data.'


class PreviewCollectionError(GlobusPortalException):
    DEFAULT_MESSAGE = 'Could not determine how to access the specified collection for Preview Mode'
    def __init__(self, message=DEFAULT_MESSAGE, **kwargs):
        super().__init__(message=message, **kwargs)
        self.code = 'BadPreviewConfig'


class ExpiredGlobusToken(GlobusPortalException):
    def __init__(self, token_name='', **kwargs):
        super().__init__(**kwargs)
        """
        :param token_name: Name of Globus Token
        """
        self.code = 'ExpiredGlobusToken'
        self.token_name = token_name
        if token_name:
            self.message = 'Your Globus Token has expired: "{}"' \
                           ''.format(token_name)
        else:
            self.message = 'Your Globus Token has expired.'


class InvalidRangeFilter(GlobusPortalException):
    def __init__(self, code='', message=''):
        """
        :param code: A short string that can be checked against, such as
            'PermissionDenied'
        :param message: A longer string that describes the problem and action
            that should be taken.
        """
        super().__init__()
        self.code = code or 'RangeFilterError'
        self.message = message or 'Invalid Range Encountered'

    def __str__(self):
        return '{}: {}'.format(self.code, self.message)

    def __repr__(self):
        return str(self)
