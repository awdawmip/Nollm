from __future__ import annotations

from time import perf_counter

from nollm_access import AccessSurfaceNavigator, PLACEMENT_SURFACE_BUDGET
from nollm_core import (
    CoreRuntime,
    GeometryAddress,
    MemoryAtom,
    PhysicalFieldScope,
    PutCommand,
    clear_surface_order_cache,
)
import nollm_core.state as core_state


SCOPE = PhysicalFieldScope("default_dream_v1", "default", (0,), 0)


def _coordinates(radius: int) -> tuple[tuple[int, int], ...]:
    return tuple(
        (q, r)
        for q in range(-radius, radius + 1)
        for r in range(-radius, radius + 1)
        if max(abs(q), abs(r), abs(q + r)) <= radius
    )


def _populate(workspace, coordinates: tuple[tuple[int, int], ...]) -> None:
    with CoreRuntime(workspace) as core:
        core.apply_batch(tuple(
            PutCommand(
                MemoryAtom(f"atom-{index}", str(index)),
                GeometryAddress("default_dream_v1", "default", 0, q, r),
            )
            for index, (q, r) in enumerate(coordinates)
        ))


def test_order_zero_budget_stops_without_building_coarser_orders(tmp_path, monkeypatch) -> None:
    _populate(tmp_path, _coordinates(2)[:11])
    clear_surface_order_cache()
    calls = []
    original = core_state.build_surface_orders

    def observed(scope, max_order, occupancy, endpoints, registry, existing_orders=()):
        calls.append(max_order)
        return original(scope, max_order, occupancy, endpoints, registry, existing_orders)

    monkeypatch.setattr(core_state, "build_surface_orders", observed)
    page = AccessSurfaceNavigator(tmp_path).begin("lazy-order-zero", SCOPE, PLACEMENT_SURFACE_BUDGET)
    assert page.selection.info.order == 0
    assert calls == [0]


def test_page_continuation_reuses_deletable_state_bound_surface_cache(tmp_path, monkeypatch) -> None:
    _populate(tmp_path, _coordinates(8))
    clear_surface_order_cache()
    calls = []
    original = core_state.build_surface_orders

    def observed(scope, max_order, occupancy, endpoints, registry, existing_orders=()):
        calls.append(max_order)
        return original(scope, max_order, occupancy, endpoints, registry, existing_orders)

    monkeypatch.setattr(core_state, "build_surface_orders", observed)
    navigator = AccessSurfaceNavigator(tmp_path)
    page = navigator.begin("lazy-page-reuse", SCOPE, PLACEMENT_SURFACE_BUDGET)
    built = tuple(calls)
    assert built == tuple(range(page.selection.info.order + 1))
    assert page.has_more
    navigator.continue_page(page)
    assert tuple(calls) == built
    clear_surface_order_cache()
    reopened = AccessSurfaceNavigator(tmp_path).begin("lazy-page-rebuild", SCOPE, PLACEMENT_SURFACE_BUDGET)
    assert reopened.selection == page.selection
    assert len(calls) > len(built)


def test_surface_cache_is_invalidated_after_mutation(tmp_path) -> None:
    first = GeometryAddress("default_dream_v1", "default", 0, 0, 0)
    second = GeometryAddress("default_dream_v1", "default", 0, 1, 0)
    with CoreRuntime(tmp_path) as core:
        core.put(MemoryAtom("first", "first"), first)
        before = core.surface_orders(SCOPE, 0)[0]
        core.put(MemoryAtom("second", "second"), second)
        after = core.surface_orders(SCOPE, 0)[0]
    assert before.native_atom_count == 1
    assert after.native_atom_count == 2


def test_small_and_dense_surface_geometry_meet_hard_ceilings(tmp_path) -> None:
    cases = (
        ("small", _coordinates(2)[:11], 5.0),
        ("dense", _coordinates(8), 15.0),
    )
    for name, coordinates, ceiling_seconds in cases:
        workspace = tmp_path / name
        _populate(workspace, coordinates)
        clear_surface_order_cache()
        started = perf_counter()
        page = AccessSurfaceNavigator(workspace).begin(name, SCOPE, PLACEMENT_SURFACE_BUDGET)
        elapsed = perf_counter() - started
        assert elapsed < ceiling_seconds
        assert page.selection.info.occupied_cell_count > 0
