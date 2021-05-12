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
from collections import defaultdict

from .shard import Shard
from .ratelimiter import Ratelimiter

from corded.objects.partials import GetGatewayBot, SessionStartLimit
from corded.helpers import int_types


class GatewayClient:
    def __init__(self, http, intents: int, shard_ids: list = None, shard_count: int = None, *, loop: AbstractEventLoop = None):
        """A client to connect to the Discord gateway.

        Args:
            http ([type]): The HTTP client to use for API requests.
            intents (int): The intents to connect with.
            shard_ids (list, optional): The shard IDs to connect with. Defaults to [0].
            shard_count (int, optional): The total number of shards being used. Defaults to 1.
            loop (AbstractEventLoop, optional): The event loop to use. Defaults to the result of asyncio.get_event_loop.
        """
        self.http = http
        self.intents = intents

        self.shard_count = shard_count or 1
        self.shard_ids = shard_ids or list(range(self.shard_count))

        self.loop = loop or get_event_loop()

        self.shards = [Shard(id, self, self.loop) for id in self.shard_ids]

        self.listeners = defaultdict(list)
        self.dispatch_middleware = []

    async def start(self):
        gateway: GetGatewayBot = await self.http.get_gateway_bot()
        limit: SessionStartLimit = gateway.session_start_limit

        limiter = Ratelimiter(limit.max_concurrency, 5)

        for shard in self.shards:
            await limiter.wait()
            await shard.connect()

    async def dispatch(self, event: str, raw_data: dict):
        if event in ["gateway_receive", "gateway_send"]:
            data = raw_data
        else:
            data = raw_data["d"]

        data = int_types(data)

        for middleware in self.dispatch_middleware:
            data = await middleware(event, data)

        for listener in self.listeners[event]:
            self.loop.create_task(listener(data))

    async def dispatch_recv(self, data: dict):
        await self.dispatch("gateway_receive", data)

        if event := data.get("t"):
            await self.dispatch(event.lower(), data)
        else:
            await self.dispatch(f"op_{data['op']}", data)

    async def dispatch_send(self, data: dict):
        await self.dispatch("gateway_send", data)

        await self.dispatch(f"op_{data['op']}", data)
