from nollm_access import (
    AccessDecision,
    AccessRecallRequest,
    AccessRuntime,
    AccessSurfaceNavigator,
    FileHandleStore,
    FileStatementStore,
    MemoryStatement,
)
from nollm_core import CoreRuntime, GeometryAddress, RecallBudget, expand_physical_coverage


def _place(access: AccessRuntime, statement_id: str, content: str, target: GeometryAddress) -> None:
    access.capture(MemoryStatement(statement_id, content))
    access.apply(AccessDecision(f"decision:{statement_id}", statement_id, "new", target_cell=target, reason_text="cross-layer fixture", decided_by="fixture"))


def test_single_entry_cross_layer_recall_path_and_wire_reopen(tmp_path) -> None:
    source = GeometryAddress("default_dream_v1", "default", 2, -7, 5)
    expansion = expand_physical_coverage(source, "coverage_down")
    target = max(expansion.members, key=lambda member: (member.weight_q16, member.target.stable_key())).target
    wrong_target = GeometryAddress("default_dream_v1", "default", 3, target.q + 40, target.r - 40)
    with CoreRuntime(tmp_path) as core:
        with AccessRuntime(core, FileStatementStore(tmp_path), FileHandleStore(tmp_path)) as access:
            _place(access, "entry", "entry", source)
            _place(access, "cross-layer", "cross-layer", target)
            _place(access, "wrong-target", "wrong-target", wrong_target)
            disabled = access.recall(AccessRecallRequest("disabled", (source,), (), (), RecallBudget(1, 32, 1, 0, 0, 16)))
            enabled = access.recall(AccessRecallRequest("enabled", (source,), (), ("coverage_down",), RecallBudget(1, 32, 1, 0, 0, 16)))
    assert {item.statement_id for item in disabled.items} == {"entry"}
    by_statement = {item.statement_id: item for item in enabled.items}
    assert set(by_statement) == {"entry", "cross-layer"}
    assert by_statement["entry"].path == ()
    assert by_statement["cross-layer"].path == ("coverage_down",)
    assert "wrong-target" not in by_statement

    navigator = AccessSurfaceNavigator(tmp_path)
    reopened = navigator.recall_entry("wire-reopen", source)
    wire = {item["statement_id"]: item for item in reopened.items}
    assert wire["cross-layer"]["path"] == ["coverage_down"]
    assert wire["cross-layer"]["path_is_not_truth_proof"] is True
    assert wire["entry"]["path"] == []
    assert "wrong-target" not in wire
    assert reopened.entry_cell == source
