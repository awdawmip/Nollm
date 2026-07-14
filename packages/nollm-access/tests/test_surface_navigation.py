import pytest

from nollm_access import (
    AccessDecision,
    AccessRuntime,
    AccessSurfaceNavigator,
    FileHandleStore,
    FileStatementStore,
    MemoryStatement,
    SurfaceBudgetProfile,
)
from nollm_core import CoreRuntime, GeometryAddress, SurfacePlane


PLANE = SurfacePlane("eisenstein_exact_v1", "default", None, 0)
BUDGET = SurfaceBudgetProfile(2, 20, 100, 1, 1, 1000, 3, 2)


def place(workspace, statement_id: str, content: str, q: int) -> None:
    core = CoreRuntime(workspace)
    store = FileStatementStore(workspace)
    access = AccessRuntime(core, store, FileHandleStore(workspace))
    statement = MemoryStatement(statement_id, content)
    access.capture(statement)
    access.apply(AccessDecision(f"d:{statement_id}", statement_id, "new", GeometryAddress("eisenstein_exact_v1", "default", 0, q, 0), reason_text="fixture", decided_by="fixture"))
    access.close()
    core.close()


def test_surface_page_previews_are_bounded_current_and_deterministic(tmp_path) -> None:
    for index in range(4):
        place(tmp_path, f"s{index}", "x" * 300, 0)
    navigator = AccessSurfaceNavigator(tmp_path)
    page = navigator.begin("op", PLANE, BUDGET)
    cell = page.cells[0]
    assert len(cell.statements) == 3
    assert all(len(item.content_utf8) == 256 for item in cell.statements)
    assert cell.truncated and cell.remaining_count == 1
    assert navigator.begin("op", PLANE, BUDGET).cells == page.cells


def test_traversal_only_accepts_shown_candidates_and_descends_to_order_zero(tmp_path) -> None:
    place(tmp_path, "alpha", "Alpha release", 0)
    navigator = AccessSurfaceNavigator(tmp_path)
    fine_budget = SurfaceBudgetProfile(8, 1, 0 + 1, 1, 1, 1, 3, 2)
    page = navigator.begin("op", PLANE, fine_budget)
    assert page.state.order == 2 and page.selection.overflow
    with pytest.raises(ValueError, match="unavailable"):
        navigator.open_surface_cell(page, "surface:invented")
    page = navigator.open_surface_cell(page, page.cells[0].candidate_id)
    assert page.state.order == 1
    page = navigator.open_surface_cell(page, page.cells[0].candidate_id)
    assert page.state.order == 0
    entry = navigator.select_entry(page, page.cells[0].candidate_id)
    assert entry.layer == 0


def test_pagination_return_and_call_limits_are_temporary(tmp_path) -> None:
    for q in range(5):
        place(tmp_path, f"s{q}", str(q), q)
    navigator = AccessSurfaceNavigator(tmp_path)
    page = navigator.begin("op", PLANE, BUDGET)
    if page.has_more:
        continued = navigator.continue_page(page)
        assert continued.state.after == page.next_after
    coarse = navigator.request_coarser_surface(page)
    opened = navigator.open_surface_cell(coarse, coarse.cells[0].candidate_id)
    returned = navigator.return_to_parent(opened)
    assert returned.state.order == coarse.state.order
    limited = SurfaceBudgetProfile(8, 20, 100, 1, 1, 1000, 3, 2, max_calls=1)
    first = navigator.begin("limited", PLANE, limited)
    with pytest.raises(RuntimeError, match="call limit"):
        navigator.page(first.state)
    assert not (tmp_path / "access" / "surface_state.json").exists()


def test_multi_entry_recall_is_canonical_bounded_and_deduplicated(tmp_path) -> None:
    place(tmp_path, "a", "Alpha one", 0)
    place(tmp_path, "b", "Alpha two", 1)
    navigator = AccessSurfaceNavigator(tmp_path)
    entries = (
        GeometryAddress("eisenstein_exact_v1", "default", 0, 0, 0),
        GeometryAddress("eisenstein_exact_v1", "default", 0, 1, 0),
    )
    result = navigator.recall_entries("r", entries, 3)
    assert {item["statement_id"] for item in result.items} == {"a", "b"}
    assert len(result.per_entry) == 2
    with pytest.raises(ValueError, match="selection limit"):
        navigator.recall_entries("r", entries, 1)
