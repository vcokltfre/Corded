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

from time import time
from asyncio import sleep


class Ratelimiter:
    def __init__(self, rate: int, per: int):
        """A ratelimiter to prevent making too many requests to the gateway.

        Args:
            rate (int): The rate at which requests can be made.
            per (int): The interval for requests.
        """

        self.rate = rate
        self.per = per
        self.current = 0
        self.current_t = time()

    async def wait(self):
        if self.current_t + 60 < time():
            self.current = 1
            self.current_t = time()
            return

        if self.current < self.rate:
            self.current += 1
            return

        await sleep(time() - self.current_t)
        self.current = 1
        self.current_t = time()
        return
