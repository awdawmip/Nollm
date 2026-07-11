from __future__ import annotations

import json
from pathlib import Path
from typing import TextIO

from nollm_core import CoreTraceEvent, TraceSink


class NullTraceSink:
    def emit(self, event: CoreTraceEvent) -> None:
        return None


class MemoryTraceSink:
    def __init__(self) -> None:
        self.events: list[CoreTraceEvent] = []

    def emit(self, event: CoreTraceEvent) -> None:
        self.events.append(event)


class JsonlTraceSink:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def emit(self, event: CoreTraceEvent) -> None:
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

    def emit(self, event: CoreTraceEvent) -> None:
        print(event, file=self.stream)


class MetricsTraceSink:
    def __init__(self) -> None:
        self.counts: dict[str, int] = {}

    def emit(self, event: CoreTraceEvent) -> None:
        self.counts[event.name] = self.counts.get(event.name, 0) + 1


class CompositeTraceSink:
    def __init__(self, *sinks: TraceSink) -> None:
        self.sinks = sinks

    def emit(self, event: CoreTraceEvent) -> None:
        for sink in self.sinks:
            try:
                sink.emit(event)
            except Exception:
                # Observability is explicitly outside Core correctness.
                continue


class TraceInspector:
    def read_jsonl(self, path: Path) -> tuple[dict[str, object], ...]:
        if not Path(path).exists():
            return ()
        records = []
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            value = json.loads(line)
            if type(value) is not dict or frozenset(value) != frozenset({"name", "fields", "stability"}):
                raise ValueError("invalid Trace JSONL record")
            records.append(value)
        return tuple(records)

    def summarize(self, records: tuple[dict[str, object], ...]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for record in records:
            name = record["name"]
            if type(name) is not str:
                raise ValueError("invalid Trace event name")
            counts[name] = counts.get(name, 0) + 1
        return dict(sorted(counts.items()))
