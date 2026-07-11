from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[4]
for package in ("nollm-core", "nollm-snapshot", "nollm-trace"):
    sys.path.insert(0, str(ROOT / "packages" / package / "src"))

from nollm_core import CoreTraceEvent  # noqa: E402
from nollm_snapshot import SnapshotService  # noqa: E402
from nollm_trace import (  # noqa: E402
    CompositeTraceSink,
    JsonlTraceSink,
    MemoryTraceSink,
    MetricsTraceSink,
    NullTraceSink,
)


class FakeStatePort:
    def __init__(self, state: bytes = b"") -> None:
        self.state = state
        self.calls: list[object] = []
        self.fail_export = False

    def export_state_bytes(self) -> bytes:
        self.calls.append(("export",))
        if self.fail_export:
            raise RuntimeError("export failed")
        return self.state

    def import_state_bytes(self, payload: bytes) -> None:
        self.calls.append(("import", payload))
        self.state = payload

class FailingTraceSink:
    def emit(self, event: CoreTraceEvent) -> None:
        raise RuntimeError(event.name)


def test_snapshot_create_uses_atomic_state_export() -> None:
    port = FakeStatePort(b"current-state")

    payload = SnapshotService().create(port)

    assert payload == b"current-state"
    assert port.calls == [("export",)]


def test_snapshot_propagates_export_failure() -> None:
    port = FakeStatePort(b"current-state")
    port.fail_export = True

    with pytest.raises(RuntimeError, match="export failed"):
        SnapshotService().create(port)

    assert port.calls == [("export",)]


def test_snapshot_clone_verify_and_structural_diff_are_policy_free() -> None:
    source = FakeStatePort(b"state-a")
    target = FakeStatePort()
    service = SnapshotService()

    assert service.clone(source, target) == b"state-a"
    assert target.state == b"state-a"
    assert service.verify(target, b"state-a")
    assert not service.structural_diff(b"state-a", b"state-a")
    assert service.structural_diff(b"state-a", b"state-b")


def test_null_trace_does_not_change_operation_result() -> None:
    def operation(sink: object) -> tuple[int, ...]:
        result = tuple(value * value for value in range(4))
        sink.emit(CoreTraceEvent("squared", {"count": len(result)}, "stable"))
        return result

    assert operation(NullTraceSink()) == operation(MemoryTraceSink())


def test_composite_trace_isolates_a_failing_sink() -> None:
    memory = MemoryTraceSink()
    metrics = MetricsTraceSink()
    event = CoreTraceEvent("cell.put", {"cell": 7}, "internal")

    CompositeTraceSink(FailingTraceSink(), memory, metrics).emit(event)

    assert memory.events == [event]
    assert metrics.counts == {"cell.put": 1}


def test_jsonl_trace_is_canonical_and_preserves_stability(tmp_path: Path) -> None:
    path = tmp_path / "trace" / "events.jsonl"

    JsonlTraceSink(path).emit(
        CoreTraceEvent("frontier", {"z": 2, "a": 1}, "experimental")
    )

    line = path.read_text(encoding="utf-8").strip()
    assert json.loads(line) == {
        "fields": {"a": 1, "z": 2},
        "name": "frontier",
        "stability": "experimental",
    }
    assert line == (
        '{"fields":{"a":1,"z":2},"name":"frontier",'
        '"stability":"experimental"}'
    )
