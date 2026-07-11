from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Mapping, Protocol


TraceStability = Literal["stable", "internal", "experimental"]


@dataclass(frozen=True)
class TraceEvent:
    name: str
    fields: Mapping[str, object]
    stability: TraceStability = "internal"


class TraceSink(Protocol):
    def emit(self, event: TraceEvent) -> None: ...


class NullTraceSink:
    def emit(self, event: TraceEvent) -> None:
        return None


def safe_emit(sink: TraceSink, event: TraceEvent) -> None:
    """Emit optional observability without affecting Core correctness."""
    try:
        sink.emit(event)
    except Exception:
        return None


class ConsistentStatePort(Protocol):
    def begin_consistent_read(self) -> object: ...

    def export_state(self, token: object) -> bytes: ...

    def import_state(self, payload: bytes) -> None: ...

    def end_consistent_read(self, token: object) -> None: ...
