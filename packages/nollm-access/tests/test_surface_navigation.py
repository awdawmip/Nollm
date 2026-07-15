import pytest

from nollm_access import AccessDecision, AccessRuntime, AccessSurfaceNavigator, FileHandleStore, FileStatementStore, MemoryStatement, SurfaceBudgetProfile
from nollm_core import CoreRuntime, GeometryAddress, MemoryAtom, PhysicalFieldScope, expand_physical_coverage


SCOPE = PhysicalFieldScope("default_dream_v1", "default", (0,), 0)
BUDGET = SurfaceBudgetProfile(2, 20, 100, 1, 1, 1000, 8, 8, 24)


def place(workspace, statement_id: str, content: str, q: int) -> None:
    place_at(workspace, statement_id, content, GeometryAddress("default_dream_v1", "default", 0, q, 0))


def place_at(workspace, statement_id: str, content: str, address: GeometryAddress) -> None:
    core = CoreRuntime(workspace)
    access = AccessRuntime(core, FileStatementStore(workspace), FileHandleStore(workspace))
    statement = MemoryStatement(statement_id, content)
    access.capture(statement)
    if address.profile_id == "default_dream_v1" and address.layer == 0:
        access.apply(AccessDecision(f"d:{statement_id}", statement_id, "new", address, reason_text="fixture", decided_by="fixture"))
    else:
        handle = core.put(MemoryAtom(statement_id, content), address)
        access.handle_store.put(statement_id, handle)
    access.close()
    core.close()


def test_surface_page_previews_are_bounded_current_and_deterministic(tmp_path) -> None:
    for index in range(4):
        place(tmp_path, f"s{index}", "x" * 300, 0)
    navigator = AccessSurfaceNavigator(tmp_path)
    page = navigator.begin("op", SCOPE, BUDGET)
    cell = page.cells[0]
    assert len(cell.statements) == 3 and all(len(item.content_utf8) == 256 for item in cell.statements)
    assert cell.truncated and cell.remaining_count == 1
    assert navigator.begin("op", SCOPE, BUDGET).cells == page.cells
    assert "dispersion_q16" not in cell.to_mapping() and "boundary_mass_q16" not in cell.to_mapping()


def test_traversal_accepts_only_shown_candidates_and_reaches_one_physical_entry(tmp_path) -> None:
    place(tmp_path, "alpha", "Alpha release", 0)
    navigator = AccessSurfaceNavigator(tmp_path)
    coarse_budget = SurfaceBudgetProfile(8, 1, 1, 1, 1, 1, 8, 8, 24)
    page = navigator.begin("op", SCOPE, coarse_budget)
    assert page.state.order == 8 and page.selection.overflow
    with pytest.raises(ValueError, match="unavailable"):
        navigator.open_surface_cell(page, "surface:invented")
    while page.state.order > 0:
        page = navigator.open_surface_cell(page, page.cells[0].candidate_id)
    physical = navigator.open_physical_entries(page, page.cells[0].candidate_id)
    resolution = navigator.select_entry(physical, physical.candidates[0].candidate_id)
    assert resolution.entry_cell == GeometryAddress("default_dream_v1", "default", 0, 0, 0)
    assert resolution.resolved_singleton
    with pytest.raises(TypeError, match="PhysicalEntryPage"):
        navigator.select_entry(page, page.cells[0].candidate_id)


def test_multiple_physical_entries_require_an_explicit_shown_choice(tmp_path) -> None:
    source = GeometryAddress("default_dream_v1", "default", 1, 0, 0)
    target = expand_physical_coverage(source, "coverage_up").members[0].target
    place_at(tmp_path, "fine", "fine physical source", source)
    core = CoreRuntime(tmp_path)
    access = AccessRuntime(core, FileStatementStore(tmp_path), FileHandleStore(tmp_path))
    statement = MemoryStatement("coarse", "coarse physical source")
    access.capture(statement)
    coarse_handle = core.put(MemoryAtom("coarse", "coarse physical source"), target)
    access.handle_store.put("coarse", coarse_handle)
    access.close()
    core.close()

    scope = PhysicalFieldScope("default_dream_v1", "default", (0, 1), 0, max_relative_layer_delta=1)
    navigator = AccessSurfaceNavigator(tmp_path)
    page = navigator.begin("multi", scope, BUDGET)
    surface = next(cell for cell in page.cells if cell.physical_source_cell_count == 2)
    physical = navigator.open_physical_entries(page, surface.candidate_id)
    assert physical.total_candidate_count == 2 and not physical.to_mapping()["resolved_singleton"]
    assert {candidate.address for candidate in physical.candidates} == {source, target}
    assert all(candidate.native_atom_count == 1 for candidate in physical.candidates)
    assert all(candidate.current_statement_preview is not None for candidate in physical.candidates)
    assert all(candidate.membership_weight_q16 > 0 for candidate in physical.candidates)
    with pytest.raises(ValueError, match="unavailable physical-entry"):
        navigator.select_entry(physical, "physical-entry:invented")
    selected = next(candidate for candidate in physical.candidates if candidate.address == source)
    resolution = navigator.select_entry(physical, selected.candidate_id)
    assert resolution.entry_cell == source and not resolution.resolved_singleton


def test_pagination_return_call_limits_and_state_are_temporary(tmp_path) -> None:
    for q in range(5):
        place(tmp_path, f"s{q}", str(q), q)
    navigator = AccessSurfaceNavigator(tmp_path)
    page = navigator.begin("operation-only", SCOPE, BUDGET)
    mapping = navigator.state_to_mapping(page.state)
    assert "query" not in str(mapping).lower() and "session" not in str(mapping).lower()
    assert navigator.state_from_mapping(mapping) == page.state
    coarse = navigator.request_coarser_surface(page)
    opened = navigator.open_surface_cell(coarse, coarse.cells[0].candidate_id)
    assert navigator.return_to_parent(opened).state.order == coarse.state.order
    limited = SurfaceBudgetProfile(8, 20, 100, 1, 1, 1000, 8, 8, 1)
    first = navigator.begin("limited", SCOPE, limited)
    with pytest.raises(RuntimeError, match="call limit"):
        navigator.page(first.state)
    assert not (tmp_path / "access" / "surface_state.json").exists()


def test_single_entry_recall_propagates_and_deduplicates_by_statement(tmp_path) -> None:
    place(tmp_path, "a", "Alpha one", 0)
    place(tmp_path, "b", "Alpha two", 1)
    navigator = AccessSurfaceNavigator(tmp_path)
    entry = GeometryAddress("default_dream_v1", "default", 0, 0, 0)
    result = navigator.recall_entry("r", entry)
    assert result.entry_cell == entry
    assert {item["statement_id"] for item in result.items} == {"a", "b"}
    assert len({item["statement_id"] for item in result.items}) == len(result.items)
    with pytest.raises(TypeError, match="entry_cell"):
        navigator.recall_entry("r", (entry,))
