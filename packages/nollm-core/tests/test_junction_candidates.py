import inspect

import pytest

from nollm_core import CoreRuntime, GeometryAddress, JunctionRequest, MemoryAtom, PhysicalFieldScope


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
