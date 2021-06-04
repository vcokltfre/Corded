from dataclasses import dataclass
from typing import Any, Literal, Optional, Union

from corded.helpers import int_types
from corded.ws.shard import Shard


Direction = Union[Literal["inbound"], Literal["outbound"]]


@dataclass
class GatewayEvent:
    shard: Shard
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
