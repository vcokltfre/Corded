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


class GatewayClient:
    def __init__(self, http, intents: int, shard_ids: list = None, shard_count: int = None, *, loop: AbstractEventLoop = None):
        self.http = http
        self.intents = intents

        self.shard_count = shard_count or 1
        self.shard_ids = shard_ids or list(range(self.shard_count))

        self.loop = loop or get_event_loop()

        self.shards = [Shard(id, self, self.loop) for id in self.shard_ids]

        self.listeners = defaultdict(list)

    async def start(self):
        gateway: GetGatewayBot = await self.http.get_gateway_bot()
        limit: SessionStartLimit = gateway.session_start_limit

        limiter = Ratelimiter(limit.max_concurrency, 5)

        for shard in self.shards:
            await limiter.wait()
            await shard.connect()

    async def dispatch(self, event: str, *args, **kwargs):
        for listener in self.listeners[event]:
            self.loop.create_task(listener(*args, **kwargs))

    async def dispatch_recv(self, data: dict):
        await self.dispatch("gateway_receive", data)

    async def dispatch_send(self, data: dict):
        await self.dispatch("gateway_send", data)
