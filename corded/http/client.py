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
from json import JSONDecodeError
from typing import Any, Literal

from aiohttp import ClientResponse, ClientSession, FormData

import corded.objects.partials as p
from corded.constants import API_URL, VERSION
from corded.errors import (
    BadRequest,
    DiscordServerError,
    Forbidden,
    HTTPError,
    NotFound,
    PayloadTooLarge,
    TooManyRequests,
    Unauthorized,
)

from .file import File
from .ratelimiter import Ratelimiter
from .route import Route

ResponseFormat = Literal["raw", "text", "json", "auto", "response"]


class HTTPClient:
    def __init__(
        self, token: str, *, url: str = None, loop: AbstractEventLoop = None
    ) -> None:
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
    async def response_as(
        response: ClientResponse, format: ResponseFormat = "json"
    ) -> Any:
        """Return a ClientResponse in a given format.

        Args:
            response (ClientResponse): The client response to get data from.
            format (str, optional): The format to use. Defaults to 'json', must be one of 'json', 'text', 'auto', 'raw'.
        """

        if format == "raw":
            return await response.read()
        if format == "json":
            return await response.json()
        if format == "text":
            return await response.text()
        if format == "auto":
            try:
                return await response.json()
            except JSONDecodeError:
                return await response.text()
        if format == "response":
            return response
        raise ValueError("Format must be one of 'json', 'text', 'auto', 'raw'")

    async def request(
        self,
        method: str,
        route: Route,
        *,
        attempts: int = None,
        expect: ResponseFormat = "json",
        **params,
    ) -> Any:
        """Make a Discord API request.

        Args:
            method (str): The HTTP method to use.
            route (Route): The Route to use for the request.
            attempts (int, optional): How many attempts to make before giving up. Defaults to 3.
            expect (str, optional): What format to expect the result in. Defaults to JSON.
        """

        attempts = attempts or 3

        if not self.session or self.session.closed:
            self.session = ClientSession(headers=self.headers)

        bucket = route.bucket

        request_headers = {}
        if "reason" in params:
            request_headers["X-Audit-Log-Reason"] = params.pop("reason")

        for i in range(attempts):
            if files := params.pop("files", []):
                if i:
                    for file in files:
                        file.seek(0)
                formdata = FormData()

                for fn, file in enumerate(files):
                    if not isinstance(file, File):
                        raise TypeError(
                            f"files must be a list of corded.File, not {file.__class__.__qualname__}"
                        )
                    # TODO: use the file name and check for dupes
                    formdata.add_field(f"file_{fn}", file.file, filename=file.filename)

                for k, v in params.pop("json", {}).items():
                    formdata.add_field(k, v)

                params["data"] = formdata

            await self.ratelimiter.acquire(bucket)

            response = await self.session.request(
                method, self.url + route.route, headers=request_headers, **params
            )

            status = response.status
            headers = response.headers

            rl_reset_after = float(headers.get("X-RateLimit-Reset-After", 0))

            # Default here is for non authenticated (and hence non ratelimited) endpoints
            rl_bucket_remaining = int(headers.get("X-RateLimit-Remaining", 1))
            rl_sleep_for = 0

            if status != 429 and rl_bucket_remaining == 0:
                rl_sleep_for = rl_reset_after

            if 200 <= status < 300:
                self.ratelimiter.release(bucket, rl_sleep_for)
                return await self.response_as(response, expect)

            if status == 429:
                if not headers.get("Via"):
                    raise TooManyRequests(429, response, "Ratelimited by cloudflare.")

                data = await self.response_as(response, "json")
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

    async def spawn_ws(self, url: str):
        if not self.session or self.session.closed:
            self.session = ClientSession(headers=self.headers)

        args = {
            "max_msg_size": 0,
            "timeout": 60,
            "autoclose": False,
            "headers": {"User-Agent": self.headers["User-Agent"]},
        }

        return await self.session.ws_connect(url, **args)

    async def close(self) -> None:
        await self.session.close()

    async def get_gateway(self) -> p.GetGateway:
        route = Route("/gateway")
        response = await self.request("get", route)

        return p.GetGateway(**response)

    async def get_gateway_bot(self) -> p.GetGatewayBot:
        route = Route("/gateway/bot")
        response = await self.request("get", route)

        session_start_limit = p.SessionStartLimit(**response["session_start_limit"])

        return p.GetGatewayBot(response["url"], response["shards"], session_start_limit)
