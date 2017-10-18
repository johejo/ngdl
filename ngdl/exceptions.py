class PortError(Exception):
    pass


class URIError(Exception):
    pass


class StatusCodeError(Exception):
    pass


class NoContentLength(Exception):
    pass


class FileSizeError(Exception):
    pass


class NoAcceptRange(Exception):
    pass


class GetResponseError(Exception):
    pass
