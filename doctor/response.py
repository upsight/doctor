class Response(object):
    """Represents a response.

    This object contains the response itself along with any additional headers
    that should be added and returned with the response data.  An instance of
    this class can be returned from a logic function in order to modify
    response headers.

    :param content: The data to be returned with the response.
    :param dict headers: A dict of response headers to include with the response
    :param int status_code: The status code for the response.
    """

    def __init__(self, content, headers=None, status_code=None):
        self.content = content
        self.headers = headers
        self.status_code = status_code
