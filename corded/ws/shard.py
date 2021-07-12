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

from asyncio import AbstractEventLoop, Task, sleep
from sys import platform
from time import time

from aiohttp import WSMessage, WSMsgType

import corded
from corded.objects.constants import GatewayCloseCodes as CloseCodes
from corded.objects.constants import GatewayOps

from .ratelimiter import Ratelimiter


class Shard:
    def __init__(self, id: int, parent: "corded.ws.GatewayClient", loop: AbstractEventLoop) -> None:
        """A shard to connect to the Discord gateway to receive and send events.

        Args:
            id (int): The shard's ID.
            parent (corded.ws.GatewayClient): The shard's parent gateway shard manager.
            loop (AbstractEventLoop): The even loop to use.
        """

        self.id = id
        self.parent = parent
        self.loop = loop

        self.url = None
        self.ws = None

        self.session = None
        self.seq = None
        self.ws_seq = None

        self.heartbeat_task = None
        self.last_heartbeat_send = None
        self.recieved_ack = True
        self.failed_heartbeats = 0
        self.latency = None

        self.pacemaker: Task = None

        self.send_limiter = Ratelimiter(120, 60, self.loop)

    def __repr__(self) -> str:
        return f"<Shard id={self.id} seq={self.seq}>"

    async def spawn_ws(self) -> None:
        """Spawn the websocket connection to the gateway."""

        self.ws = await self.parent.http.spawn_ws(self.url)

    async def connect(self) -> None:
        """Create a connection to the Discord gateway."""

        if not self.url:
            self.url = (await self.parent.http.get_gateway()).url

        await self.spawn_ws()

        if self.session:
            await self.resume()

        await self.start_reader()

    async def close(self) -> None:
        """Gracefully close the connection."""

        self.failed_heartbeats = 0

        if self.ws and not self.ws.closed:
            await self.ws.close()

        if self.pacemaker and not self.pacemaker.cancelled():
            self.pacemaker.cancel()

    async def send(self, data: dict) -> None:
        """Send data to the gateway.

        Args:
            data (dict): The data to send.
        """

        await self.send_limiter.wait()

        self.loop.create_task(self.parent.dispatch_send(self, data))
        await self.ws.send_json(data)

    async def identify(self) -> None:
        """Sends an identfy payload to the gateway."""

        await self.send(
            {
                "op": GatewayOps.IDENTIFY,
                "d": {
                    "token": self.parent.http.token,
                    "properties": {
                        "$os": platform,
                        "$browser": "Corded",
                        "$device": "Corded",
                    },
                    "intents": self.parent.intents,
                    "shard": [self.id, self.parent.shard_count],
                },
            }
        )

    async def resume(self) -> None:
        """Resume an existing connection with the gateway."""

        await self.send(
            {
                "op": GatewayOps.RESUME,
                "d": {
                    "token": self.parent.http.token,
                    "session_id": self.session,
                    "seq": self.seq,
                },
            }
        )

    async def heartbeat(self) -> None:
        """Send a heartbeat to the gateway."""

        self.last_heartbeat_send = time()

        await self.send({"op": GatewayOps.HEARTBEAT, "d": self.seq})

        if self.seq:
            self.seq += 1
        else:
            self.seq = 1

    async def dispatch(self, data: dict) -> None:
        """Dispatch events."""

        await self.parent.dispatch_recv(self, data)

        op = data["op"]

        if op == GatewayOps.HELLO:
            self.pacemaker = self.loop.create_task(
                self.start_pacemaker(data["d"]["heartbeat_interval"])
            )
            await self.identify()
        elif op == GatewayOps.ACK:
            self.latency = time() - self.last_heartbeat_send
            self.recieved_ack = True
        elif op == GatewayOps.RECONNECT:
            await self.close()
            await self.connect()

    async def handle_disconnect(self, code: int) -> None:
        """Handle the gateway disconnecting correctly."""

        if code in [
            CloseCodes.NOT_AUTHENTICATED,
            CloseCodes.AUTHENTICATION_FAILED,
            CloseCodes.INVALID_API_VERSION,
            CloseCodes.INVALID_INTENTS,
            CloseCodes.DISALLOWED_INTENTS,
        ]:
            await self.parent.panic(code)

        if code in [
            CloseCodes.INVALID_SEQ,
            CloseCodes.RATE_LIMITED,
            CloseCodes.SESSION_TIMEOUT,
        ]:
            self.session = None

            if code == CloseCodes.RATE_LIMITED:
                self.url = None

        self.seq = None

        await self.close()
        await self.connect()

    async def start_reader(self) -> None:
        """Start a loop constantly reading from the gateway."""

        async for message in self.ws:
            message: WSMessage

            if message.type == WSMsgType.TEXT:
                message_data = message.json()

                if s := message_data.get("s"):
                    self.ws_seq = s

                await self.dispatch(message_data)

        await self.handle_disconnect(self.ws.close_code)

    async def start_pacemaker(self, delay: float) -> None:
        """A loop to constantly heartbeat at an interval given by the gateway."""

        delay = delay / 1000

        while True:
            if not self.recieved_ack:
                self.failed_heartbeats += 1

                await self.close()
                await self.resume()
                return

            await self.heartbeat()
            self.recieved_ack = False

            await sleep(delay)
