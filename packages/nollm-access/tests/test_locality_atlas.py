from time import perf_counter

from nollm_access import AccessMemoryLoop, LocalityAtlas, MemoryStatement
from nollm_core import CoreRuntime, GeometryAddress, MemoryAtom


def placement(statement_id, candidate_id):
    return {"schema_version": "nollm_openclaw_surface_placement_v1", "outcome": "apply", "decision": {"statement_id": statement_id, "action": "expand_surface", "candidate_id": candidate_id, "reason_text": "fixture"}}


def test_empty_atlas_is_finite_stable_and_relation_neutral(tmp_path):
    with AccessMemoryLoop(tmp_path) as loop:
        first = loop.build_locality_atlas("empty", 8)
        second = loop.build_locality_atlas("empty", 8)
    assert isinstance(first, LocalityAtlas)
    assert first == second
    assert 1 <= len(first.candidates) <= 8
    assert all(not item.occupied and not item.representative_statements for item in first.candidates)
    assert first.nodes and first.paths
    assert not any(key in str(first.to_mapping()).lower() for key in ("topic", "source_index", "query", "embedding"))


def test_atlas_projects_real_boundary_and_representative_statement(tmp_path):
    with AccessMemoryLoop(tmp_path) as loop:
        candidate = loop.placement_candidates(None, "first")[0]
        statement = MemoryStatement("tokyo", "今天东京下雨了。")
        loop.apply_placement(statement, placement(statement.statement_id, candidate["candidate_id"]), "first")
        atlas = loop.build_locality_atlas("atlas", 12)
    occupied = [item for item in atlas.candidates if item.occupied]
    assert len(occupied) == 1
    assert occupied[0].boundary is True
    assert occupied[0].free_face_count == 6
    assert occupied[0].representative_statements[0]["statement_id"] == "tokyo"


def test_atlas_fingerprint_invalidates_after_mutation_and_read_is_write_free(tmp_path):
    with AccessMemoryLoop(tmp_path) as loop:
        before = loop.build_locality_atlas("before")
        candidate = loop.placement_candidates(None, "mutate")[0]
        loop.apply_placement(MemoryStatement("one", "one"), placement("one", candidate["candidate_id"]), "mutate")
        after = loop.build_locality_atlas("after")
    assert before.core_state_sha256 != after.core_state_sha256
    assert before.atlas_fingerprint != after.atlas_fingerprint
    with CoreRuntime(tmp_path) as core:
        state = core.export_state_bytes()
    with AccessMemoryLoop(tmp_path) as loop:
        loop.build_locality_atlas("read-only")
    with CoreRuntime(tmp_path) as core:
        assert core.export_state_bytes() == state


def test_large_atlas_covers_every_field_cell_without_projection_sampling(tmp_path):
    cells = tuple(GeometryAddress("default_dream_v1", "default", 0, q, 0) for q in range(-150, 150))
    with CoreRuntime(tmp_path) as core:
        for index in range(1000):
            core.put(MemoryAtom(f"atom-{index}", str(index)), cells[index % len(cells)])
        before = core.export_state_bytes()
    started = perf_counter()
    with AccessMemoryLoop(tmp_path) as loop:
        atlas = loop.build_locality_atlas("large", 512)
    elapsed = perf_counter() - started
    assert atlas.occupied_field_cell_count == 300
    assert atlas.covered_field_cell_count == 300
    assert atlas.uncovered_field_cell_count == 0
    assert atlas.selected_aggregation_order == 0
    assert atlas.region_count == 300
    assert atlas.overflow is False
    assert len(atlas.nodes) == len(atlas.paths) == len(atlas.candidates) == 300
    assert all(1 <= len(path.node_ids) <= 3 for path in atlas.paths)
    assert elapsed <= 2.0
    with CoreRuntime(tmp_path) as core:
        assert core.export_state_bytes() == before


def test_atlas_budget_overflow_is_explicit_and_never_samples(tmp_path):
    cells = tuple(GeometryAddress("default_dream_v1", "default", 0, q, 0) for q in range(40))
    with CoreRuntime(tmp_path) as core:
        for index, address in enumerate(cells):
            core.put(MemoryAtom(f"atom-{index}", str(index)), address)
        before = core.export_state_bytes()
    with AccessMemoryLoop(tmp_path) as loop:
        atlas = loop.build_locality_atlas("overflow", 8)
    assert atlas.overflow is True
    assert atlas.selected_aggregation_order is None
    assert atlas.occupied_field_cell_count == atlas.uncovered_field_cell_count == 40
    assert atlas.covered_field_cell_count == atlas.region_count == 0
    assert atlas.candidates == atlas.nodes == atlas.paths == ()
    assert len(atlas.order_projection_counts) == 9
    assert all(count > 8 for count in atlas.order_projection_counts)
    with CoreRuntime(tmp_path) as core:
        assert core.export_state_bytes() == before
