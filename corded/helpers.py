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

from re import compile
from typing import Union

INT = compile(r"^\d+$")

Types = Union[dict, list, int, str, bool, float]


def int_types(data: Types) -> Types:
    if isinstance(data, (int, str, bool, float)):
        if isinstance(data, str) and INT.match(data):
            return int(data)
        return data
    if isinstance(data, dict):
        return {k: int_types(v) for k, v in data.items()}
    if isinstance(data, list):
        return [int_types(v) for v in data]


class BitField:
    def __init__(self, value: int) -> None:
        self.value = value

    def __getitem__(self, bit: int) -> int:
        return self.value >> bit & 1

    def __setitem__(self, bit: int, state: bool) -> None:
        if state:
            self.value |= 1 << bit
        else:
            self.value &= ~(1 << bit)

    def __int__(self) -> int:
        return self.value
