from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class EventContext:
    event: str
    raw_data: dict[str, Any]
    raw_body: bytes | None = None
    event_headers: dict[str, str] = field(default_factory=dict)
