from dataclasses import dataclass
from typing import Any, Literal, Optional, Union, Dict

from corded.helpers import int_types
import corded


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
    def typed_data(self):
        return int_types(self.d) if self.d else None

    @property
    def dispatch_name(self):
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
        "direct_message_typing": 1 << 14
    }

    def __setattr__(self, name, value):
        if name in self.valid.keys():
            super(Intents, self).__setattr__("value", self.value + self.valid[name])
            super(Intents, self).__setattr__(name, value)
        else:
            raise Exception(f"{name}, is not a valid intent")

    @classmethod
    def all(cls):
        """A classmethod that will enable all intents including privileged ones

        Returns:
            Intents: The Intents instance that was created
        """
        intents = cls.__new__(cls)
        super(Intents, cls).__setattr__(intents, "value", (1 << sum(cls.valid.values()).bit_length()) - 1)
        return intents

    @classmethod
    def default(cls):
        """A classmethod that will enable all intents excluding privileged ones

        Returns:
            Intents: The Intents instance that was created
        """
        intents = cls.__new__(cls)
        super(Intents, cls).__setattr__(intents, "value", (1 << sum(cls.valid.values()).bit_length()) - 259)
        return intents