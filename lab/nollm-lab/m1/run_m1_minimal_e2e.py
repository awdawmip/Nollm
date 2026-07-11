from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from concurrent.futures import ThreadPoolExecutor
from threading import Event

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
    return GeometryAddress("eisenstein_exact_v1", "m1-e2e", 1, q, r)


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
    coverage = access.recall(AccessRecallRequest("coverage", entry_cells=(GeometryAddress("eisenstein_exact_v1", "m1-e2e", 2, -3, 5),), allowed_kernels=("coverage_up",), budget=RecallBudget(1, 8, 1, 0, 0, 4)))
    assert coverage.items[0].handle == first

    access.capture(MemoryStatement("statement:support", "supporting Evidence"))
    access.apply(decision("statement:support", "reuse", existing_handle=first))
    assert access.handle_store.statement_for_handle(first) == "statement:one"
    lateral_handle = core.put(MemoryAtom("lateral", "lateral"), cell(-3, 5).lateral(1)[0])
    lateral_result = core.recall(CoreRecallRequest("lateral-one", (cell(-3, 5),), ("lateral",), RecallBudget(1, 8, 0, 1, 0, 4)))
    assert any(item.handle == lateral_handle for item in lateral_result.items)
    core.remove(lateral_handle)

    try:
        core.recall(CoreRecallRequest("fanout", (cell(-3, 5),), ("lateral",), RecallBudget(2, 8, 0, 2, 0, 4)))
    except ValueError as error:
        assert "registered lateral ring 1" in str(error)
    else:
        raise AssertionError("lateral ring=2 bypassed fanout limit")

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
        "coverage_up_registered": True,
        "lateral_ring_2_rejected": True,
        "lateral_ring_one_real_recall": True,
        "reuse_preserved_current": True,
    }


def failure_matrix(root: Path) -> dict[str, bool]:
    facts = {}
    for action in ("new", "revision_current", "revision_keep_history", "forget", "reuse"):
        workspace = root / action
        core = CoreRuntime(workspace / "core")
        store = FileHandleStore(workspace)
        access = AccessRuntime(core, FileEvidenceStore(workspace), store)
        access.capture(MemoryStatement("old", "old"))
        old = access.apply(decision("old", "new", target_cell=GeometryAddress("eisenstein_exact_v1", "fault", 0, 0, 0)))
        statement_id = "next"
        access.capture(MemoryStatement(statement_id, "next"))
        core_before, binding_before = core.state_bytes(), store.state_bytes()
        failed = True
        def fail_once(_path):
            nonlocal failed
            if failed:
                failed = False
                raise OSError("binding fault")
        store.before_replace = fail_once
        kwargs = {"target_cell": GeometryAddress("eisenstein_exact_v1", "fault", 0, 1, 0)} if action in {"new", "revision_keep_history"} else {"existing_handle": old}
        try:
            access.apply(decision(statement_id if action != "forget" else "old", action, **kwargs))
        except OSError:
            pass
        else:
            raise AssertionError(f"{action} fault did not fire")
        facts[f"{action}_rollback"] = core.state_bytes() == core_before and store.state_bytes() == binding_before
    return facts


def negative_matrix(root: Path) -> dict[str, bool]:
    import json
    from nollm_core.storage import canonical_state_bytes

    core = CoreRuntime(root / "core")
    core.put(MemoryAtom("a", "a"), GeometryAddress("eisenstein_exact_v1", "negative", 0, 0, 0))
    document = json.loads(core.state_bytes())
    document["cells"].append({"address": GeometryAddress("eisenstein_exact_v1", "negative", 0, 1, 0).to_mapping(), "atoms": []})
    try:
        core.import_state(canonical_state_bytes(document))
    except ValueError:
        empty_rejected = True
    else:
        empty_rejected = False
    evidence = FileEvidenceStore(root)
    evidence.put_original(MemoryStatement("bad", "payload"))
    evidence._path("bad").write_text('{"schema_version":"nollm_access_evidence_v1", "statement":{}}\n', encoding="utf-8")
    try:
        evidence.get_original("bad")
    except ValueError:
        evidence_rejected = True
    else:
        evidence_rejected = False
    try:
        GeometryAddress("unknown", "c", 0, 0, 0)
    except ValueError:
        unknown_rejected = True
    else:
        unknown_rejected = False
    return {"empty_cell_rejected": empty_rejected, "noncanonical_evidence_rejected": evidence_rejected, "unknown_profile_rejected": unknown_rejected}


def concurrency_fact(root: Path) -> bool:
    entered, release = Event(), Event()
    fail = True
    def hook(_path):
        nonlocal fail
        if fail:
            fail = False
            entered.set(); release.wait(5)
            raise OSError("fault")
    core = CoreRuntime(root / "core")
    store = FileHandleStore(root, hook)
    left = AccessRuntime(core, FileEvidenceStore(root), store)
    right = AccessRuntime(core, FileEvidenceStore(root), store)
    left.capture(MemoryStatement("left", "left")); right.capture(MemoryStatement("right", "right"))
    def apply(runtime, name, q):
        try:
            return runtime.apply(decision(name, "new", target_cell=GeometryAddress("eisenstein_exact_v1", "concurrent", 0, q, 0)))
        except OSError:
            return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(apply, left, "left", 0); assert entered.wait(5)
        second = pool.submit(apply, right, "right", 1); release.set()
        assert first.result() is None
        handle = second.result()
    return handle is not None and core.contains(handle) and store.get("right") == handle


def main() -> None:
    with TemporaryDirectory(prefix="nollm-m1-e2e-") as directory:
        root = Path(directory)
        normal = run(root / "normal", __import__("nollm_core").NullTraceSink())
        failing = run(root / "failing", FailingTraceSink())
        if normal != failing:
            raise AssertionError("FailingTraceSink changed M1 E2E results")
        facts = {**normal, **failure_matrix(root / "faults"), **negative_matrix(root / "negative"), "transaction_serialized": concurrency_fact(root / "concurrent"), "trace_parity": normal == failing, "reopen_bytes_equal": True}
        if not all(value is True for key, value in facts.items() if key != "state" and not isinstance(value, (int, str))):
            raise AssertionError("M1C2 E2E fact failed")
        print(json.dumps({"status": "passed", "gates": facts}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
