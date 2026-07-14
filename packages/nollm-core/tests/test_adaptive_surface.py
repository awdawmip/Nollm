import inspect

import pytest

from nollm_core import CoreRuntime, GeometryAddress, MemoryAtom, SurfacePlane


PLANE = SurfacePlane("eisenstein_exact_v1", "default", None, 0)


def cell(layer: int, q: int, r: int) -> GeometryAddress:
    return GeometryAddress("eisenstein_exact_v1", "default", layer, q, r)


def populated(runtime: CoreRuntime) -> None:
    runtime.put(MemoryAtom("a", "alpha payload must not define surface geometry"), cell(0, 0, 0))
    runtime.put(MemoryAtom("b", "office payload must not define surface geometry"), cell(0, 8, 0))


def test_orders_are_repeated_coverage_projections_and_keep_native_separate(tmp_path) -> None:
    with CoreRuntime(tmp_path) as runtime:
        populated(runtime)
        first_parent = runtime.surface_page(PLANE, 1, None, 8).cells[0].address
        runtime.put(MemoryAtom("native-upper", "upper"), first_parent)
        infos = runtime.surface_orders(PLANE, 2)
        order_zero = runtime.surface_page(PLANE, 0, None, 8)
        order_one = runtime.surface_page(PLANE, 1, None, 8)
        order_two = runtime.surface_page(PLANE, 2, None, 32)

    assert [info.order for info in infos] == [0, 1, 2]
    assert infos[0].occupied_cell_count == 2
    assert infos[1].occupied_cell_count > infos[0].occupied_cell_count
    assert infos[2].occupied_cell_count > 0
    assert [item.address for item in order_zero.cells] == [cell(0, 0, 0), cell(0, 8, 0)]
    upper = next(item for item in order_one.cells if item.address == first_parent)
    assert upper.native_occupancy_count == 1
    assert upper.aggregate_occupancy_count >= 1
    assert all(item.address.layer == -2 for item in order_two.cells)
    assert "payload_utf8" not in inspect.getsource(__import__("nollm_core.surface", fromlist=["build_surface_orders"]).build_surface_orders)


def test_source_can_contribute_to_multiple_parents_and_descent_is_not_a_tree(tmp_path) -> None:
    with CoreRuntime(tmp_path) as runtime:
        runtime.put(MemoryAtom("a", "a"), cell(0, 0, 0))
        parents = runtime.surface_page(PLANE, 1, None, 8).cells
        memberships = []
        for parent in parents:
            descent = runtime.surface_descend(PLANE, 1, parent.address, None, 8)
            if any(item.projection.address == cell(0, 0, 0) for item in descent.cells):
                memberships.append(parent.address)

    assert len(parents) == 3
    assert len(memberships) == 3
    assert len(set(memberships)) == 3


def test_surface_pagination_is_stable_without_duplicates_or_omissions(tmp_path) -> None:
    with CoreRuntime(tmp_path) as runtime:
        for q in range(12):
            runtime.put(MemoryAtom(f"a{q}", str(q)), cell(0, q, 0))
        expected = runtime.surface_page(PLANE, 0, None, 32).cells
        after = None
        actual = []
        while True:
            page = runtime.surface_page(PLANE, 0, after, 3)
            actual.extend(page.cells)
            if not page.has_more:
                break
            assert page.next_after is not None
            after = page.next_after

    assert actual == list(expected)
    assert len({item.address for item in actual}) == len(actual)


def test_surface_rebuilds_after_mutation_import_and_reopen(tmp_path) -> None:
    runtime = CoreRuntime(tmp_path)
    populated(runtime)
    before_bytes = runtime.export_state_bytes()
    before = runtime.surface_page(PLANE, 2, None, 64)
    handle = runtime.put(MemoryAtom("c", "c"), cell(0, 16, 0))
    changed = runtime.surface_page(PLANE, 2, None, 64)
    assert changed != before
    runtime.remove(handle)
    assert runtime.surface_page(PLANE, 2, None, 64) == before
    runtime.put(MemoryAtom("d", "d"), cell(0, 24, 0))
    runtime.import_state_bytes(before_bytes)
    assert runtime.surface_page(PLANE, 2, None, 64) == before
    runtime.close()

    with CoreRuntime(tmp_path) as reopened:
        assert reopened.surface_page(PLANE, 2, None, 64) == before
        assert reopened.export_state_bytes() == before_bytes


def test_surface_contract_rejects_wrong_plane_order_and_tokens(tmp_path) -> None:
    with CoreRuntime(tmp_path) as runtime:
        populated(runtime)
        with pytest.raises(TypeError, match="plane"):
            runtime.surface_orders({}, 2)
        with pytest.raises(ValueError, match="between 0 and 2"):
            runtime.surface_orders(PLANE, 3)
        with pytest.raises(ValueError, match="requested Surface order"):
            runtime.surface_page(PLANE, 0, cell(-1, 0, 0), 8)
        with pytest.raises(ValueError, match="limit"):
            runtime.surface_page(PLANE, 0, None, 0)
