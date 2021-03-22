"""
MIT License

Copyright (c) 2021 vcokltfre

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from asyncio import AbstractEventLoop, get_event_loop, sleep
from aiohttp import ClientSession, ClientResponse

from corded.constants import API_URL, VERSION
from corded.errors import HTTPError, BadRequest, Unauthorized, Forbidden, NotFound, PayloadTooLarge, TooManyRequests, DiscordServerError

from .ratelimiter import Ratelimiter
from .route import Route


class HTTPClient:
    def __init__(self, token: str, *, url: str = None, loop: AbstractEventLoop = None):
        """An HTTP client to make Discord API requests, observing ratelimits.

        Args:
            token (str): The bot token to make requests with.
            url (str, optional): The URL of the Discord API. Defaults to corded.constants.API_URL.
            loop (AbstractEventLoop, optional): The event loop to use. Defaults to asyncio.get_event_loop().
        """

        self.token = token
        self.url = url or API_URL
        self.loop = loop or get_event_loop()

        self.headers = {
            "Authorization": f"Bot {self.token}",
            "User-Agent": f"DiscordBot (Corded, https://github.com/vcokltfre/corded, version: {VERSION})",
            "X-RateLimit-Precision": "millisecond",
        }

        self.ratelimiter = Ratelimiter(self.loop)
        self.session: ClientSession = None

        self.errors = {
            "_": HTTPError,
            400: BadRequest,
            401: Unauthorized,
            403: Forbidden,
            404: NotFound,
            413: PayloadTooLarge,
        }

    @staticmethod
    async def response_as(response: ClientResponse, format: str = None):
        """Return a ClientResponse in a given format.

        Args:
            response (ClientResponse): The client response to get data from.
            format (str, optional): The format to use. Defaults to 'json', must be one of 'json', 'text', 'auto', 'raw'.
        """

        if format == "raw":
            return response.read()
        if format == "json":
            return await response.json()
        if format == "text":
            return await response.text()
        if format == "auto":
            try:
                return await response.json()
            except:
                return await response.text()
        raise ValueError("Format must be one of 'json', 'text', 'auto', 'raw'")

    async def request(self, method: str, route: Route, *, attempts: int = None, expect: str = None, **params):
        """Make a Discord API request.

        Args:
            method (str): The HTTP method to use.
            route (Route): The Route to use for the request.
            attempts (int, optional): How many attempts to make before giving up. Defaults to 3.
            expect (str, optional): What format to expect the result in. Defaults to JSON.
        """

        attempts = attempts or 3
        expect = expect or "json"

        if not self.session or self.session.closed:
            self.session = ClientSession(headers=self.headers)

        bucket = route.bucket

        headers = {}
        if "reason" in params:
            headers["X-Audit-Log-Reason"] = params.pop("reason")

        for i in range(attempts):
            await self.ratelimiter.acquire(bucket)

            response = await self.session.request(method, self.url + route.route, **params)

            status = response.status
            headers = response.headers

            rl_reset_after = float(headers.get("X-RateLimit-Reset-After"))
            rl_bucket_remaining = int(headers.get("X-RateLimit-Remaining"))
            rl_sleep_for = 0

            if status != 429 and rl_bucket_remaining == 0:
                rl_sleep_for = rl_reset_after

            if 200 <= status < 300:
                self.ratelimiter.release(bucket, rl_sleep_for)
                return await self.response_as(response, expect)

            if status == 429:
                if not headers.get("Via"):
                    raise TooManyRequests(429, response, "Ratelimited by cloudflare.")

                data = await self.response(response, "json")
                is_global = data.get("global", False)
                rl_sleep_for = data.get("retry_after")

                if is_global:
                    self.ratelimiter.lock_globally(rl_sleep_for)

            elif status >= 500:
                rl_sleep_for = 1 + i * 2

            else:
                self.ratelimiter.release(bucket, rl_sleep_for)
                raise self.errors.get(status, self.errors["_"])(response)

            if i == attempts - 1:
                self.ratelimiter.release(bucket, rl_sleep_for)
                continue

            await sleep(rl_sleep_for)

        self.ratelimiter.release(bucket)

        if status >= 500:
            raise DiscordServerError(response)

        raise self.errors.get(status, self.errors["_"])(response)
