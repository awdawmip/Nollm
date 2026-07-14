import inspect

from nollm_access import SurfaceBudgetProfile, select_active_surface
from nollm_core import CoreRuntime, GeometryAddress, MemoryAtom, SurfaceOrderInfo, SurfacePlane


PLANE = SurfacePlane("eisenstein_exact_v1", "default", None, 0)


def budget(max_cells: int, max_units: int = 1000) -> SurfaceBudgetProfile:
    return SurfaceBudgetProfile(2, 20, max_cells, 3, 5, max_units, 3, 2)


def populate(runtime: CoreRuntime, count: int) -> None:
    for q in range(count):
        runtime.put(
            MemoryAtom(f"a{q}", f"payload {q}"),
            GeometryAddress("eisenstein_exact_v1", "default", 0, q * 8, 0),
        )


def structural_infos() -> tuple[SurfaceOrderInfo, ...]:
    return tuple(
        SurfaceOrderInfo(PLANE, order, count, (count + 1) // 2, 0, count * 65536, order)
        for order, count in enumerate((40, 12, 4))
    )


def test_selects_finest_order_that_satisfies_exact_structural_cost(tmp_path) -> None:
    selected = select_active_surface(structural_infos(), budget(12))
    assert selected.info.order == 1
    assert selected.estimated_pages == (selected.info.occupied_cell_count + 1) // 2
    assert selected.projection_units == selected.estimated_pages * 3 + selected.info.occupied_cell_count * 5
    assert not selected.overflow


def test_overflow_uses_hard_max_order_without_semantic_fallback(tmp_path) -> None:
    with CoreRuntime(tmp_path) as runtime:
        populate(runtime, 3)
        infos = runtime.surface_orders(PLANE, 2)
    selected = select_active_surface(infos, budget(1, 1))
    assert selected.info.order == 2
    assert selected.info.overflow
    assert selected.overflow


def test_selection_has_no_query_session_or_statement_input_and_reopens_identically(tmp_path) -> None:
    assert tuple(inspect.signature(select_active_surface).parameters) == ("infos", "budget")
    with CoreRuntime(tmp_path) as runtime:
        populate(runtime, 5)
        first = select_active_surface(runtime.surface_orders(PLANE, 2), budget(20))
    with CoreRuntime(tmp_path) as reopened:
        second = select_active_surface(reopened.surface_orders(PLANE, 2), budget(20))
    assert first == second


def test_different_fixed_budgets_can_change_order(tmp_path) -> None:
    infos = structural_infos()
    fine = select_active_surface(infos, budget(40))
    coarse = select_active_surface(infos, budget(12))
    assert fine.info.order == 0
    assert coarse.info.order == 1
