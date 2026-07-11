from __future__ import annotations

import json
from pathlib import Path
from typing import TextIO

from nollm_core import TraceEvent, TraceSink


class MemoryTraceSink:
    def __init__(self) -> None:
        self.events: list[TraceEvent] = []

    def emit(self, event: TraceEvent) -> None:
        self.events.append(event)


class JsonlTraceSink:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def emit(self, event: TraceEvent) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "name": event.name,
            "fields": dict(event.fields),
            "stability": event.stability,
        }
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")))
            handle.write("\n")


class ConsoleTraceSink:
    def __init__(self, stream: TextIO | None = None) -> None:
        self.stream = stream

    def emit(self, event: TraceEvent) -> None:
        print(event, file=self.stream)


class MetricsTraceSink:
    def __init__(self) -> None:
        self.counts: dict[str, int] = {}

    def emit(self, event: TraceEvent) -> None:
        self.counts[event.name] = self.counts.get(event.name, 0) + 1


class CompositeTraceSink:
    def __init__(self, *sinks: TraceSink) -> None:
        self.sinks = sinks

    def emit(self, event: TraceEvent) -> None:
        for sink in self.sinks:
            try:
                sink.emit(event)
            except Exception:
                # Observability is explicitly outside Core correctness.
                continue
