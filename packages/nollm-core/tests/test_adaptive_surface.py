import inspect

import pytest

from nollm_core import (
    CoreRuntime,
    GeometryAddress,
    MemoryAtom,
    PhysicalFieldScope,
    SurfaceAggregateAddress,
)


SCOPE = PhysicalFieldScope("default_dream_v1", "default", (0,), 0)


def cell(layer: int, q: int, r: int) -> GeometryAddress:
    return GeometryAddress("default_dream_v1", "default", layer, q, r)


def dense(runtime: CoreRuntime, radius: int = 5) -> int:
    count = 0
    for q in range(-radius, radius + 1):
        for r in range(-radius, radius + 1):
            if max(abs(q), abs(r), abs(q + r)) <= radius:
                runtime.put(MemoryAtom(f"a{count}", "payload must not define Surface geometry"), cell(0, q, r))
                count += 1
    return count


def test_physical_and_surface_address_domains_are_separate(tmp_path) -> None:
    with CoreRuntime(tmp_path) as runtime:
        runtime.put(MemoryAtom("a", "a"), cell(0, 0, 0))
        address = runtime.surface_page(SCOPE, 0, None, 8).cells[0].address
        assert type(address) is SurfaceAggregateAddress
        assert address.reference_physical_layer == 0 and address.aggregation_order == 0
        with pytest.raises(TypeError, match="invalid PutCommand"):
            runtime.put(MemoryAtom("bad", "bad"), address)


def test_order_zero_includes_every_native_physical_layer_in_scope(tmp_path) -> None:
    scope = PhysicalFieldScope("default_dream_v1", "default", (-1, 0, 1), 0, max_relative_layer_delta=1)
    with CoreRuntime(tmp_path) as runtime:
        expected = (cell(-1, 0, 0), cell(0, 3, 0), cell(1, 7, -2))
        for index, address in enumerate(expected):
            runtime.put(MemoryAtom(f"a{index}", str(index)), address)
        page = runtime.surface_page(scope, 0, None, 32)
    visible = {source for projection in page.cells for source in projection.source_cells}
    assert visible == set(expected)
    assert sum(projection.aggregate_atom_count for projection in page.cells) == 3


def test_orders_zero_through_eight_really_coarsen_dense_field(tmp_path) -> None:
    with CoreRuntime(tmp_path) as runtime:
        native_count = dense(runtime, 8)
        infos = runtime.surface_orders(SCOPE, 8)
    counts = [info.occupied_cell_count for info in infos]
    areas = [info.grid.observation_area_ratio_q32 for info in infos]
    assert native_count == 217
    assert [info.order for info in infos] == list(range(9))
    assert counts[0] == native_count and any(count < counts[0] for count in counts[1:])
    assert all(right > left for left, right in zip(areas, areas[1:]))
    assert all(info.scope == SCOPE for info in infos)


def test_overlap_descent_has_no_unique_parent(tmp_path) -> None:
    with CoreRuntime(tmp_path) as runtime:
        dense(runtime, 4)
        order_zero = runtime.surface_page(SCOPE, 0, None, 256).cells
        order_one = runtime.surface_page(SCOPE, 1, None, 256).cells
        memberships = {projection.address: 0 for projection in order_zero}
        for parent in order_one:
            descent = runtime.surface_descend(SCOPE, parent.address, None, 256)
            for child in descent.cells:
                memberships[child.projection.address] += 1
    assert max(memberships.values()) > 1


def test_surface_pagination_and_rebuild_are_stable(tmp_path) -> None:
    runtime = CoreRuntime(tmp_path)
    dense(runtime, 3)
    before_bytes = runtime.export_state_bytes()
    before = runtime.surface_page(SCOPE, 4, None, 256)
    after = None
    actual = []
    while True:
        page = runtime.surface_page(SCOPE, 4, after, 3)
        actual.extend(page.cells)
        if not page.has_more:
            break
        after = page.next_after
    assert actual == list(before.cells)
    handle = runtime.put(MemoryAtom("new", "new"), cell(0, 20, 0))
    assert runtime.surface_page(SCOPE, 4, None, 256) != before
    runtime.remove(handle)
    assert runtime.surface_page(SCOPE, 4, None, 256) == before
    runtime.import_state_bytes(before_bytes)
    runtime.close()
    with CoreRuntime(tmp_path) as reopened:
        assert reopened.surface_page(SCOPE, 4, None, 256) == before
        assert reopened.export_state_bytes() == before_bytes


def test_surface_contract_is_query_free_and_rejects_unsupported_scope(tmp_path) -> None:
    with pytest.raises(ValueError, match="unsupported"):
        PhysicalFieldScope("default_dream_v1", "default", (0, 9), 0, max_relative_layer_delta=8)
    source = inspect.getsource(__import__("nollm_core.surface", fromlist=["build_surface_orders"]).build_surface_orders)
    assert "payload_utf8" not in source and "query" not in inspect.signature(__import__("nollm_core.surface", fromlist=["build_surface_orders"]).build_surface_orders).parameters
    with CoreRuntime(tmp_path) as runtime:
        runtime.put(MemoryAtom("a", "a"), cell(0, 0, 0))
        with pytest.raises(TypeError, match="scope"):
            runtime.surface_orders({}, 2)
        with pytest.raises(ValueError, match="between 0 and 8"):
            runtime.surface_orders(SCOPE, 9)
        with pytest.raises(TypeError, match="SurfaceAggregateAddress"):
            runtime.surface_page(SCOPE, 0, cell(0, 0, 0), 8)
