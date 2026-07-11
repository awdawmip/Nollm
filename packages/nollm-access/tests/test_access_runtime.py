import pytest

from nollm_access import (
    AccessDecision,
    AccessRecallRequest,
    AccessRuntime,
    FileEvidenceStore,
    FileHandleStore,
    MemoryStatement,
)
from nollm_core import (
    BridgeSpec,
    CoreRuntime,
    GeometryAddress,
    GeometryAnchor,
    RecallBudget,
)


def cell(q: int, r: int) -> GeometryAddress:
    return GeometryAddress("eisenstein_exact_v1", "chart", 1, q, r)


def runtime(tmp_path) -> tuple[AccessRuntime, CoreRuntime]:
    core = CoreRuntime(tmp_path / "core")
    return AccessRuntime(core, FileEvidenceStore(tmp_path), FileHandleStore(tmp_path)), core


def decision(statement_id: str, action: str, **values: object) -> AccessDecision:
    return AccessDecision("decision:" + statement_id + ":" + action, statement_id, action, reason_text="explicit fixture decision", decided_by="fixture", **values)


def test_capture_new_reuse_defer_and_forget(tmp_path) -> None:
    access, core = runtime(tmp_path)
    statement = MemoryStatement("s1", "原始 Evidence", "file:one", ("context:one",))
    before = core.export_state_bytes()
    access.capture(statement)
    assert core.export_state_bytes() == before

    handle = access.apply(decision("s1", "new", target_cell=cell(-3, 5)))
    assert access.saved_handle("s1") == handle
    after_new = core.export_state_bytes()

    access.capture(MemoryStatement("s1-reuse", "explicit reuse Evidence"))
    assert access.apply(decision("s1-reuse", "reuse", existing_handle=handle)) == handle
    assert core.export_state_bytes() == after_new

    access.capture(MemoryStatement("s-defer", "deferred Evidence"))
    assert access.apply(decision("s-defer", "defer")) is None
    assert core.export_state_bytes() == after_new

    removed = access.apply(decision("s1", "forget", existing_handle=handle))
    assert removed.atom_id == "s1"
    assert core.placement_count() == 0


def test_revision_current_and_keep_history_are_access_semantics(tmp_path) -> None:
    access, core = runtime(tmp_path)
    access.capture(MemoryStatement("original", "version one"))
    original = access.apply(decision("original", "new", target_cell=cell(0, 0)))

    access.capture(MemoryStatement("current", "version two"))
    current = access.apply(decision("current", "revision_current", existing_handle=original))
    assert current == original
    assert core.get(current).payload_utf8 == "version two"
    assert access.saved_handle("current") == current

    access.capture(MemoryStatement("history", "version retained separately"))
    historical = access.apply(decision("history", "revision_keep_history", target_cell=cell(1, 0)))
    assert historical != current
    assert core.placement_count() == 2

    result = access.recall(
        AccessRecallRequest(
            "recall",
            entry_cells=(cell(0, 0), cell(1, 0)),
            allowed_kernels=(),
            budget=RecallBudget(0, 4, 0, 0, 0, 4),
        )
    )
    assert {(item.statement_id, item.evidence_utf8) for item in result.items} == {
        ("current", "version two"),
        ("history", "version retained separately"),
    }


def test_stitch_and_unstitch_use_explicit_geometry(tmp_path) -> None:
    access, core = runtime(tmp_path)
    bridge = BridgeSpec(
        "bridge",
        GeometryAnchor("from", (cell(0, 0),)),
        GeometryAnchor("to", (cell(5, -5),)),
        1 << 15,
        "normal",
        1,
        2,
    )
    assert access.apply(decision("bridge-action", "stitch", bridge_spec=bridge)) == bridge
    assert core.bridges() == (bridge,)
    assert access.apply(decision("bridge-action", "unstitch", bridge_spec=bridge)) == bridge
    assert core.bridges() == ()


def test_decisions_require_explicit_geometry_or_handle() -> None:
    with pytest.raises(ValueError, match="target_cell"):
        decision("missing-cell", "new")
    with pytest.raises(ValueError, match="existing_handle"):
        decision("missing-handle", "reuse")


def test_missing_binding_is_an_explicit_access_fallback(tmp_path) -> None:
    access, core = runtime(tmp_path)
    handle = core.put(__import__("nollm_core").MemoryAtom("orphan", "payload"), cell(0, 0))
    result = access.recall(
        AccessRecallRequest(
            "orphan-recall",
            entry_handles=(handle,),
            budget=RecallBudget(0, 1, 0, 0, 0, 1),
        )
    )
    assert result.items[0].fallback_error == "binding_missing"
    assert result.items[0].evidence_utf8 is None
