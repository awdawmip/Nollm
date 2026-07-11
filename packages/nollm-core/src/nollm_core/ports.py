from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal, Mapping, Protocol


TraceStability = Literal["stable", "internal", "experimental"]


@dataclass(frozen=True)
class CoreTraceEvent:
    name: str
    fields: Mapping[str, object]
    stability: TraceStability = "internal"

    def __post_init__(self) -> None:
        if type(self.name) is not str or not self.name:
            raise TypeError("trace event name must be a non-empty string")
        if self.stability not in {"stable", "internal", "experimental"}:
            raise ValueError("invalid trace stability")
        values = dict(self.fields)
        if any(type(key) is not str or not key for key in values):
            raise TypeError("trace field names must be non-empty strings")
        if any(type(value) not in {str, int, bool, type(None)} for value in values.values()):
            raise TypeError("Core trace fields must contain immutable scalar values")
        object.__setattr__(self, "fields", MappingProxyType(dict(sorted(values.items()))))


class TraceSink(Protocol):
    def emit(self, event: CoreTraceEvent) -> None: ...
