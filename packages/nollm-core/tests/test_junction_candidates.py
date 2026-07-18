import inspect

import pytest

from nollm_core import CoreRuntime, GeometryAddress, JunctionRequest, MemoryAtom, PhysicalFieldScope, RelationGroupJunctionRequest


SCOPE = PhysicalFieldScope("default_dream_v1", "default", (0,), 0, max_relative_layer_delta=0)


def cell(q, r):
    return GeometryAddress("default_dream_v1", "default", 0, q, r)


def request(primary=(), contacts=(), **values):
    return JunctionRequest(SCOPE, tuple(sorted(primary, key=lambda item: item.stable_key())), tuple(sorted(contacts, key=lambda item: item.stable_key())), **values)


def test_empty_field_returns_stable_origin_frontier_without_writing(tmp_path):
    with CoreRuntime(tmp_path) as core:
        before = core.export_state_bytes()
        first = core.junction_candidates(request(max_radius=2))
        second = core.junction_candidates(request(max_radius=2))
        assert first == second
        assert first[0].cell == cell(0, 0)
        assert core.export_state_bytes() == before


def test_boundary_candidates_report_free_faces_and_prefer_primary_proximity(tmp_path):
    with CoreRuntime(tmp_path) as core:
        core.put(MemoryAtom("a", "alpha"), cell(0, 0))
        result = core.junction_candidates(request([cell(0, 0)], max_radius=2))
    assert result
    assert result[0].primary_max_distance == 1
    assert result[0].boundary is True
    assert result[0].occupied_neighbor_count == 1
    assert result[0].free_face_count == 5


def test_multi_locality_distance_and_far_contact_remain_primary_bounded(tmp_path):
    with CoreRuntime(tmp_path) as core:
        for index, address in enumerate((cell(0, 0), cell(2, 0), cell(20, 0))):
            core.put(MemoryAtom(str(index), str(index)), address)
        result = core.junction_candidates(request([cell(0, 0), cell(2, 0)], [cell(20, 0)], max_radius=2))
    assert all(min(max(abs(item.cell.q - p.q), abs(item.cell.r - p.r), abs((item.cell.q + item.cell.r) - (p.q + p.r))) for p in (cell(0, 0), cell(2, 0))) <= 2 for item in result)
    assert all(item.contact_max_distance >= 16 for item in result)


def test_negative_coordinates_active_radius_and_budget_are_enforced(tmp_path):
    with CoreRuntime(tmp_path) as core:
        core.put(MemoryAtom("negative", "negative"), cell(-3, 1))
        result = core.junction_candidates(request([cell(-3, 1)], max_radius=2, candidate_limit=3, active_hex_radius=4))
    assert 1 <= len(result) <= 3
    assert all(max(abs(item.cell.q), abs(item.cell.r), abs(item.cell.q + item.cell.r)) <= 4 for item in result)


def test_contract_rejects_semantic_or_noncanonical_inputs():
    assert "statement" not in inspect.signature(JunctionRequest).parameters
    assert "query" not in inspect.signature(JunctionRequest).parameters
    with pytest.raises(ValueError, match="canonical"):
        JunctionRequest(SCOPE, (cell(1, 0), cell(0, 0)))
    with pytest.raises(ValueError, match=r"\[1,8\]"):
        request(max_radius=9)


def relation_request(groups, **values):
    canonical = tuple(tuple(sorted(group, key=lambda item: item.stable_key())) for group in groups)
    return RelationGroupJunctionRequest(SCOPE, canonical, **values)


def test_relation_group_junction_balances_primary_and_contact(tmp_path):
    with CoreRuntime(tmp_path) as core:
        core.put(MemoryAtom("left", "left"), cell(0, 0))
        core.put(MemoryAtom("right", "right"), cell(4, 0))
        result = core.relation_group_junction_candidates(relation_request(((cell(0, 0),), (cell(4, 0),))))
    assert result[0].cell == cell(2, 0)
    assert result[0].group_distances == (2, 2)
    assert result[0].groups_within_contact_radius == 2
    assert result[0].all_groups_realized is True


def test_relation_group_order_is_geometry_invariant_and_contact_is_causal(tmp_path):
    groups = ((cell(0, 0),), (cell(4, 0),))
    with CoreRuntime(tmp_path) as core:
        for index, address in enumerate((cell(0, 0), cell(4, 0))):
            core.put(MemoryAtom(str(index), str(index)), address)
        forward = core.relation_group_junction_candidates(relation_request(groups))
        reverse = core.relation_group_junction_candidates(relation_request(tuple(reversed(groups))))
        ablated = core.relation_group_junction_candidates(relation_request((groups[0],)))
    assert tuple(item.cell for item in forward) == tuple(item.cell for item in reverse)
    assert forward[0].cell != ablated[0].cell


def test_relation_group_uses_min_cell_distance_and_reports_no_bounded_junction(tmp_path):
    with CoreRuntime(tmp_path) as core:
        for index, address in enumerate((cell(0, 0), cell(1, 0), cell(20, 0))):
            core.put(MemoryAtom(str(index), str(index)), address)
        local = core.relation_group_junction_candidates(relation_request(((cell(0, 0), cell(1, 0)), (cell(4, 0),))))
        far = core.relation_group_junction_candidates(relation_request(((cell(0, 0),), (cell(20, 0),))))
    assert local[0].group_distances[0] == min(
        max(abs(local[0].cell.q - target.q), abs(local[0].cell.r - target.r), abs((local[0].cell.q + local[0].cell.r) - (target.q + target.r)))
        for target in (cell(0, 0), cell(1, 0))
    )
    assert far == ()


def test_relation_group_contract_is_semantic_blind_and_bounded():
    parameters = inspect.signature(RelationGroupJunctionRequest).parameters
    assert "statement" not in parameters and "query" not in parameters and "lens" not in parameters
    with pytest.raises(ValueError, match="one to four groups"):
        RelationGroupJunctionRequest(SCOPE, ())
    with pytest.raises(ValueError, match="one to four cells"):
        RelationGroupJunctionRequest(SCOPE, ((cell(0, 0),) * 5,))
