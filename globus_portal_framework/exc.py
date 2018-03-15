
class PreviewException(Exception):
    """
    Exceptions when trying to fetch data from Globus Preview
    """
    def __init__(self, code='', message=''):
        """
        :param code: A short string that can be checked against, such as
            'PermissionDenied'
        :param message: A longer string that describes the problem and action
            that should be taken.
        """
        self.code = code or 'UnexpectedError'
        self.message = message or 'There was an unexpected error ' \
                                  'when fetching preview data.'

    def __str__(self):
        return '{}: {}'.format(self.code, self.message)

    def __repr__(self):
        return str(self)


class PreviewPermissionDenied(PreviewException):
    def __init__(self):
        self.code = 'PermissionDenied'
        self.message = 'You do not have access to view this data'


class PreviewNotFound(PreviewException):
    def __init__(self):
        self.code = 'NotFound'
        self.message = 'Could not find file on the preview server'


class PreviewServerError(PreviewException):
    def __init__(self, http_code, server_error):
        self.code = 'ServerError'
        self.message = 'There was a problem with the Preview Server'
        self.http_code = http_code
        self.server_error = server_error

    def __str__(self):
        return '{}\nHttpCode: {}\nServer Text: {}'.format(super().__str__(),
                                                          self.http_code,
                                                          self.server_error)


class PreviewBinaryData(PreviewException):
    def __init__(self):
        self.code = 'BinaryData'
        self.message = 'Preview is unable to display binary data.'
