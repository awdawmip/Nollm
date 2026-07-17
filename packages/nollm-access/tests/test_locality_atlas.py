from nollm_access import AccessMemoryLoop, LocalityAtlas, MemoryStatement
from nollm_core import CoreRuntime


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
