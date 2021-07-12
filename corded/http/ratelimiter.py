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

from asyncio import AbstractEventLoop, Event, Lock, get_event_loop


class Ratelimiter:
    def __init__(self, loop: AbstractEventLoop = None) -> None:
        """A ratelimit handler for API requests.

        Args:
            loop (AbstractEventLoop, optional): The event loop to use. Defaults to the result of asyncio.get_event_loop.
        """

        self.loop = loop or get_event_loop()

        self.locks = {}

        self.global_lock = Event(loop=self.loop)
        self.global_lock.set()

    async def acquire(self, bucket: str) -> None:
        """Acquire the ratelimit lock on a given bucket.

        Args:
            bucket (str): The bucket to acquire the lock on.
        """

        lock = self.locks.get(bucket)

        if not lock:
            lock = Lock(loop=self.loop)
            self.locks[bucket] = lock

        await lock.acquire()
        await self.global_lock.wait()

    def release(self, bucket: str, after: float = 0) -> None:
        """Release the ratelimit lock on a given bucket

        Args:
            bucket (str): The bucket to release the lock on.
        """

        lock = self.locks[bucket]

        self.loop.call_later(after, lock.release)

    def lock_globally(self, duration: float) -> None:
        """Lock the global ratelimit lock for a set duration.

        Args:
            duration (float): The duration to lock the lock for in seconds.
        """

        self.global_lock.clear()
        self.loop.call_later(duration, self.global_lock.set)
