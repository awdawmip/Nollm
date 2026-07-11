from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from nollm_access import (
    AccessDecision,
    AccessRecallRequest,
    AccessRuntime,
    FileEvidenceStore,
    FileHandleStore,
    MemoryStatement,
)
from nollm_core import (
    AtomHandle,
    BridgeSpec,
    CoreRecallRequest,
    CoreRuntime,
    GeometryAddress,
    GeometryAnchor,
    MemoryAtom,
    RecallBudget,
    TraceEvent,
)
from nollm_snapshot import SnapshotService


class FailingTraceSink:
    def emit(self, event: TraceEvent) -> None:
        raise RuntimeError(event.name)


def cell(q: int, r: int) -> GeometryAddress:
    return GeometryAddress("exact", "m1-e2e", 1, q, r)


def decision(statement_id: str, action: str, **values: object) -> AccessDecision:
    return AccessDecision(
        f"decision:{statement_id}:{action}",
        statement_id,
        action,
        reason_text="explicit fixture decision",
        decided_by="fixture",
        **values,
    )


def run(root: Path, sink: object) -> dict[str, object]:
    core = CoreRuntime(root / "core", trace_sink=sink)
    access = AccessRuntime(core, FileEvidenceStore(root), FileHandleStore(root))
    snapshot = SnapshotService()

    access.capture(MemoryStatement("statement:one", "原始 Evidence one", "file:one"))
    first = access.apply(decision("statement:one", "new", target_cell=cell(-3, 5)))
    assert isinstance(first, AtomHandle)
    recalled = access.recall(
        AccessRecallRequest(
            "recall:one",
            entry_cells=(cell(-3, 5),),
            budget=RecallBudget(0, 4, 0, 0, 0, 4),
        )
    )
    assert recalled.items[0].evidence_utf8 == "原始 Evidence one"

    access.capture(MemoryStatement("statement:current", "Evidence revision current", "file:two"))
    current = access.apply(decision("statement:current", "revision_current", existing_handle=first))
    assert current == first
    frozen = snapshot.create(core)

    moved = core.move(first, cell(4, -6))
    bridge = BridgeSpec(
        "bridge:m1",
        GeometryAnchor("from", (cell(4, -6),)),
        GeometryAnchor("to", (cell(7, -9),)),
        1 << 15,
        "normal",
        1,
        2,
    )
    access.apply(decision("bridge:m1", "stitch", bridge_spec=bridge))
    assert core.contains(moved) and core.bridges() == (bridge,)

    snapshot.restore(core, frozen)
    assert core.contains(first)
    assert not core.contains(moved)
    assert core.bridges() == ()
    restored_recall = access.recall(
        AccessRecallRequest(
            "recall:restored",
            entry_handles=(first,),
            budget=RecallBudget(0, 4, 0, 0, 0, 4),
        )
    )
    assert restored_recall.items[0].statement_id == "statement:current"
    assert restored_recall.items[0].evidence_utf8 == "Evidence revision current"

    access.capture(MemoryStatement("statement:defer", "deferred Evidence"))
    before_defer = core.state_bytes()
    assert access.apply(decision("statement:defer", "defer")) is None
    assert core.state_bytes() == before_defer

    access.capture(MemoryStatement("statement:history", "retained historical Evidence"))
    historical = access.apply(
        decision("statement:history", "revision_keep_history", target_cell=cell(0, 1))
    )
    assert isinstance(historical, AtomHandle)
    assert core.placement_count() == 2

    assert not hasattr(core, "get_by_global_id")
    assert "source_window" not in CoreRecallRequest.__dataclass_fields__
    try:
        decision("invalid", "new")
    except ValueError:
        pass
    else:
        raise AssertionError("new decision without explicit target_cell was accepted")
    try:
        BridgeSpec(
            "invalid",
            GeometryAnchor("from-invalid", (cell(0, 0),)),
            GeometryAnchor("to-invalid", (cell(1, 0),)),
            1 << 15,
            "normal",
            1,
            65,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("over-budget BridgeSpec was accepted")

    reopened = CoreRuntime(root / "core")
    assert reopened.state_bytes() == core.state_bytes()
    return {
        "state": core.state_bytes().decode("utf-8"),
        "placement_count": core.placement_count(),
        "restored_statement": restored_recall.items[0].statement_id,
        "restored_evidence": restored_recall.items[0].evidence_utf8,
        "defer_unchanged": True,
        "history_retained": core.contains(first) and core.contains(historical),
    }


def main() -> None:
    with TemporaryDirectory(prefix="nollm-m1-e2e-") as directory:
        root = Path(directory)
        normal = run(root / "normal", __import__("nollm_core").NullTraceSink())
        failing = run(root / "failing", FailingTraceSink())
        if normal != failing:
            raise AssertionError("FailingTraceSink changed M1 E2E results")
        print(json.dumps({"status": "passed", "result": normal}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
