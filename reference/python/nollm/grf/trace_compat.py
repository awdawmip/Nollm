"""Legacy GRF trace contract retained outside active distributions."""

from dataclasses import dataclass
from typing import Mapping, Protocol


@dataclass(frozen=True)
class TraceEvent:
    name: str
    fields: Mapping[str, object]
    stability: str = "internal"


class TraceSink(Protocol):
    def emit(self, event: TraceEvent) -> None: ...


class NullTraceSink:
    def emit(self, event: TraceEvent) -> None:
        return None


def safe_emit(sink: TraceSink, event: TraceEvent) -> None:
    try:
        sink.emit(event)
    except Exception:
        return
