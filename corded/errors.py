from aiohttp import ClientResponse


class CordedError(Exception):
    pass


# HTTP Errors


class HTTPError(CordedError):
    def __init__(self, response: ClientResponse) -> None:
        self.response = response


class BadRequest(HTTPError):
    pass


class Unauthorized(HTTPError):
    pass


class Forbidden(HTTPError):
    pass


class NotFound(HTTPError):
    pass


class PayloadTooLarge(HTTPError):
    pass


class TooManyRequests(HTTPError):
    pass


class DiscordServerError(HTTPError):
    pass
