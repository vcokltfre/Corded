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

from datetime import datetime


class Object:
    def __init__(self, snowflake: int) -> None:
        """Represents a basic Discord object that has an ID.

        Allows for easy accessing of all parts of the ID and timestamp.

        Args:
            snowflake (int): The snowflake ID of the object.
        """

        self.snowflake = self.id = snowflake

        timestamp, worker, process, increment = self.deconstruct(snowflake)

        self.timestamp = timestamp
        self.worker = worker
        self.process = process
        self.increment = increment

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__qualname__} timestamp={self.timestamp}"
            f" worker={self.worker} process={self.process} increment={self.increment}>"
        )

    @staticmethod
    def deconstruct(snowflake: int) -> tuple:
        """Deconstruct a snowflake into its component parts.

        Args:
            snowflake (int): The snowflake to deconstruct.

        Returns:
            Tuple[int, int, int, int]: The parts of the snowflake.
        """

        timestamp = (snowflake >> 22) + 1420070400000
        worker = (snowflake & 0x3E0000) >> 17
        process = (snowflake & 0x1F000) >> 12
        increment = snowflake & 0xFFF

        return (timestamp, worker, process, increment)

    @property
    def isotime(self) -> str:
        """Return the ISO timestamp of the snowflake."""

        return datetime.fromtimestamp(self.timestamp).isoformat()
