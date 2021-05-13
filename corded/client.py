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

from asyncio import AbstractEventLoop, get_event_loop
from typing import Union, List

from .http import HTTPClient
from .ws import GatewayClient


class CordedClient:
    def __init__(self, token: str, intents: int, *, shard_ids: int = None, shard_count: int = None, loop: AbstractEventLoop = None):
        """A combined client that can make HTTP requests and connect to the gateway.

        Args:
            token (str): The token to use for API requests and connecting.
            intents (int): The intents to use while connecting to the gateway.
            loop (AbstractEventLoop, optional): The even loop to use. Defaults to asyncio.get_event_loop.
        """

        self.token = token
        self.intents = intents
        self.loop = loop or get_event_loop()

        self.http = HTTPClient(token, loop=self.loop)
        self.gateway = GatewayClient(self.http, self.intents, shard_ids, shard_count, loop=self.loop)

    def start(self):
        """Make a blocking call to start the Gateway connection."""

        self.loop.run_until_complete(self.gateway.start())

    def on(self, *events: List[str]):
        def wrapper(func):
            nonlocal events
            if not events:
                events = [func.__name__]
            for event in events:
                self.gateway.listeners[event].append(func)
            return func
        return wrapper

    def middleware(self, func):
        self.gateway.dispatch_middleware.append(func)
        return func
