from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Literal, Optional, Tuple, Union

import corded
from corded.helpers import int_types

Direction = Union[Literal["inbound"], Literal["outbound"]]


@dataclass
class GatewayEvent:
    shard: "corded.ws.shard.Shard"
    direction: Direction
    op: int
    d: Optional[Any]
    s: Optional[int] = None
    t: Optional[str] = None

    @property
    def typed_data(self) -> Any:
        return int_types(self.d) if self.d else None

    @property
    def dispatch_name(self) -> str:
        return (self.t or f"op_{self.op}").lower()


class Intents:
    """Represents a discord intents flag
    Allows for easier passing of intents to the gateway

    """

    value: int = 0
    valid: Dict[str, int] = {
        "guilds": 1 << 0,
        "guild_members": 1 << 1,
        "guild_bans": 1 << 2,
        "guild_emojis": 1 << 3,
        "guild_integrations": 1 << 4,
        "guild_webhooks": 1 << 5,
        "guild_invites": 1 << 6,
        "guild_voice_states": 1 << 7,
        "guild_presences": 1 << 8,
        "guild_messages": 1 << 9,
        "guild_message_reactions": 1 << 10,
        "guild_message_typing": 1 << 11,
        "direct_messages": 1 << 12,
        "direct_message_reactions": 1 << 13,
        "direct_message_typing": 1 << 14,
    }

    def __init__(self) -> None:
        for flag in self.valid.keys():
            super(Intents, self).__setattr__(flag, False)

    def __setattr__(self, name: str, value: bool) -> None:
        if name in self.valid.keys():
            if value is True:
                super(Intents, self).__setattr__("value", self.value + self.valid[name])
                super(Intents, self).__setattr__(name, value)
            elif value is False and getattr(self, name) is True:
                super(Intents, self).__setattr__("value", self.value - self.valid[name])
                super(Intents, self).__setattr__(name, value)
        else:
            raise Exception(f"{name}, is not a valid intent")

    def __iter__(self) -> Tuple[str, Any]:
        for key, value in self.__dict__.items():
            if key == "value":
                continue
            yield (key, value)

    def __hash__(self) -> int:
        return hash(self.value)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} value={self.value}>"

    def __eq__(self, other) -> bool:
        return isinstance(other, self.__class__) and self.value == other.value

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    @classmethod
    def all(cls) -> Intents:
        """A classmethod that will enable all intents including privileged ones

        Returns:
            Intents: The Intents instance that was created
        """
        intents = cls.__new__(cls)
        for flag in cls.valid.keys():
            cls.__setattr__(intents, flag, True)

        return intents

    @classmethod
    def default(cls) -> Intents:
        """A classmethod that will enable all intents excluding privileged ones

        Returns:
            Intents: The Intents instance that was created
        """
        intents = cls.__new__(cls)
        for flag in cls.valid.keys():
            cls.__setattr__(intents, flag, True)

        intents.guild_members = False
        intents.guild_presences = False

        return intents
