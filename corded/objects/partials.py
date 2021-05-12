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

from dataclasses import dataclass, field


@dataclass
class GetGateway:
    url: str

@dataclass
class SessionStartLimit:
    total: int
    remaining: int
    reset_after: int
    max_concurrency: int

@dataclass
class GetGatewayBot:
    url: str
    shards: int
    session_start_limit: SessionStartLimit

@dataclass
class User:
    id: int
    username: str
    discriminator: int
    avatar: str = field(default=None)
    bot: bool = field(default_factory=bool)
    system: bool = field(default_factory=bool)
    mfa_enabled: bool = field(default_factory=bool)
    flags: int = field(default_factory=int)
    premium_type: int = field(default_factory=int)
    public_flags: int = field(default_factory=int)
