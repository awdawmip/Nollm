import inspect

from nollm_access import SurfaceBudgetProfile, select_active_surface
from nollm_core import CoreRuntime, GeometryAddress, MemoryAtom, PhysicalFieldScope


SCOPE = PhysicalFieldScope("default_dream_v1", "default", (0,), 0)


def budget(max_cells: int, max_units: int = 10000) -> SurfaceBudgetProfile:
    return SurfaceBudgetProfile(8, 20, max_cells, 3, 5, max_units, 8, 8, 24)


def populate_dense(runtime: CoreRuntime, radius: int) -> None:
    index = 0
    for q in range(-radius, radius + 1):
        for r in range(-radius, radius + 1):
            if max(abs(q), abs(r), abs(q + r)) <= radius:
                runtime.put(MemoryAtom(f"a{index}", str(index)), GeometryAddress("default_dream_v1", "default", 0, q, r))
                index += 1


def test_selects_finest_affordable_order_from_real_core_infos(tmp_path) -> None:
    with CoreRuntime(tmp_path) as runtime:
        populate_dense(runtime, 8)
        infos = runtime.surface_orders(SCOPE, 8)
    selected = select_active_surface(infos, budget(100))
    expected = next(info for info in infos if info.occupied_cell_count <= 100)
    assert selected.info == expected and selected.info.order > 0
    assert not selected.overflow


def test_overflow_uses_configured_hard_max_without_semantic_fallback(tmp_path) -> None:
    with CoreRuntime(tmp_path) as runtime:
        populate_dense(runtime, 2)
        infos = runtime.surface_orders(SCOPE, 8)
    selected = select_active_surface(infos, budget(1, 1))
    assert selected.info.order == 8 and selected.overflow and selected.info.overflow


def test_selection_is_query_agnostic_and_reopens_identically(tmp_path) -> None:
    assert tuple(inspect.signature(select_active_surface).parameters) == ("infos", "budget")
    with CoreRuntime(tmp_path) as runtime:
        populate_dense(runtime, 4)
        first = select_active_surface(runtime.surface_orders(SCOPE, 8), budget(50))
    with CoreRuntime(tmp_path) as reopened:
        second = select_active_surface(reopened.surface_orders(SCOPE, 8), budget(50))
    assert first == second


def test_budget_contract_contains_no_entry_fanout() -> None:
    fields = set(SurfaceBudgetProfile.__dataclass_fields__)
    assert fields == {"page_size", "max_pages", "max_surface_cells", "page_overhead_units", "cell_preview_units", "max_projection_units", "max_descent_depth", "hard_max_order", "max_calls"}
