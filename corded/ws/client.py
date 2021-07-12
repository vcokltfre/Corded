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
from collections import defaultdict

from corded.objects.gateway import GatewayEvent
from corded.objects.partials import GetGatewayBot, SessionStartLimit

from .ratelimiter import Ratelimiter
from .shard import Shard


class GatewayClient:
    def __init__(
        self,
        http,
        intents: int,
        shard_ids: list = None,
        shard_count: int = None,
        *,
        loop: AbstractEventLoop = None,
    ) -> None:
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

    async def panic(self, code) -> None:
        raise SystemExit(f"Shard error code: {code}")

    async def start(self) -> None:
        gateway: GetGatewayBot = await self.http.get_gateway_bot()
        limit: SessionStartLimit = gateway.session_start_limit

        limiter = Ratelimiter(limit.max_concurrency, 5, self.loop)

        for shard in self.shards:
            await limiter.wait()
            self.loop.create_task(shard.connect())

        while True:
            await sleep(0)

    async def dispatch(self, event: GatewayEvent) -> None:
        for middleware in self.dispatch_middleware:
            event = await middleware(event)

            if not event:
                return

            if not isinstance(event, GatewayEvent):
                raise TypeError(
                    f"Type of event returned by middleware {middleware.__name__}, {event.__class__.__qualname__}, is not a valid GatewayEvent."
                )

        all_listeners = [
            *self.listeners[event.dispatch_name],
            *(
                self.listeners["gateway_send"]
                if event.direction == "outbound"
                else self.listeners["gateway_receive"]
            ),
            *self.listeners["*"],
        ]

        for listener in all_listeners:
            self.loop.create_task(listener(event))

    async def dispatch_recv(self, shard: Shard, data: dict) -> None:
        await self.dispatch(GatewayEvent(shard, "inbound", **data))

    async def dispatch_send(self, shard: Shard, data: dict) -> None:
        await self.dispatch(GatewayEvent(shard, "outbound", **data))
