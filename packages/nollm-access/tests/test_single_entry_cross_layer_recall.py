from nollm_access import (
    AccessDecision,
    AccessRecallRequest,
    AccessRuntime,
    AccessSurfaceNavigator,
    FileHandleStore,
    FileStatementStore,
    MemoryStatement,
    SurfaceBudgetProfile,
)
from nollm_core import CoreRuntime, GeometryAddress, MemoryAtom, PhysicalFieldScope, RecallBudget, clear_physical_coverage_cache, expand_physical_coverage


def _place(access: AccessRuntime, statement_id: str, content: str, target: GeometryAddress) -> None:
    access.capture(MemoryStatement(statement_id, content))
    handle = access.core.put(MemoryAtom(statement_id, content), target)
    access.handle_store.put(statement_id, handle)


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

    scope = PhysicalFieldScope("default_dream_v1", "default", (2, 3), 3, max_relative_layer_delta=1)
    budget = SurfaceBudgetProfile(8, 8, 64, 1, 1, 256, 1, 1, 8)
    page = navigator.begin("explicit-entry", scope, budget)
    surface = next(cell for cell in page.cells if {item.handle.geometry_address for item in cell.statements} >= {source, target})
    physical = navigator.open_physical_entries(page, surface.candidate_id)
    assert physical.total_candidate_count >= 2
    selected = next(candidate for candidate in physical.candidates if candidate.address == source)
    resolution = navigator.select_entry(physical, selected.candidate_id)
    assert resolution.entry_cell == source and not resolution.resolved_singleton
    explicit = navigator.recall_entry("explicit-wire-reopen", resolution.entry_cell)
    explicit_wire = {item["statement_id"]: item for item in explicit.items}
    assert explicit_wire["cross-layer"]["path"] == ["coverage_down"]
    assert "wrong-target" not in explicit_wire

    clear_physical_coverage_cache()
    replayed = navigator.recall_entry("wire-cache-clear", source)
    assert [(item["statement_id"], item["path"]) for item in replayed.items] == [
        (item["statement_id"], item["path"]) for item in reopened.items
    ]


def test_large_coordinate_single_entry_cross_layer_recall_is_reopen_stable(tmp_path) -> None:
    source = GeometryAddress("default_dream_v1", "default", 4, 10**9, -10**9)
    expansion = expand_physical_coverage(source, "coverage_up")
    target = max(expansion.members, key=lambda member: (member.weight_q16, member.target.stable_key())).target
    with CoreRuntime(tmp_path) as core:
        with AccessRuntime(core, FileStatementStore(tmp_path), FileHandleStore(tmp_path)) as access:
            _place(access, "large-entry", "large entry", source)
            _place(access, "large-cross-layer", "large cross layer", target)
            result = access.recall(AccessRecallRequest("large", (source,), (), ("coverage_up",), RecallBudget(1, 32, 1, 0, 0, 16)))
    by_statement = {item.statement_id: item for item in result.items}
    assert by_statement["large-entry"].path == ()
    assert by_statement["large-cross-layer"].path == ("coverage_up",)
    clear_physical_coverage_cache()
    reopened = AccessSurfaceNavigator(tmp_path).recall_entry("large-reopen", source)
    wire = {item["statement_id"]: item for item in reopened.items}
    assert wire["large-cross-layer"]["path"] == ["coverage_up"]
