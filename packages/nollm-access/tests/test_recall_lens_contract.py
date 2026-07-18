from copy import deepcopy

import pytest

from nollm_access import AccessMemoryLoop, DREAM_SCULPTOR_SCHEMA_VERSION, LocalityAtlas, validate_dream_sculptor_plans


CAPTURE = {
    "capture_id": "capture-one",
    "user_utf8": "今天东京下雨了。",
    "assistant_utf8": "知道了。",
    "captured_epoch_ms": 1_784_275_200_000,
    "timezone_offset_minutes": 480,
}


def plan(atlas, path_ids=None, leaf_ids=None, unresolved=False, action="new_local"):
    path_ids = [atlas.paths[0].path_id] if path_ids is None else path_ids
    leaf_ids = [atlas.candidates[0].candidate_id] if leaf_ids is None else leaf_ids
    if unresolved:
        path_ids, leaf_ids = [], []
    return {
        "draft_id": "d1",
        "content_utf8": "2026年7月17日东京下雨了。",
        "source_capture_ids": ["capture-one"],
        "lenses": [{
            "lens_id": "lens-date",
            "future_query": "2026年7月17日发生了什么？",
            "basis_spans": [{"capture_id": "capture-one", "role": "user", "start": 0, "end": 8, "quote_utf8": "今天东京下雨了。"}],
            "atlas_path_ids": path_ids,
            "leaf_locality_candidate_ids": leaf_ids,
            "unresolved": unresolved,
        }],
        "action": action,
        "existing_handle": None,
        "reason_text": "new complete proposition",
    }


def test_sculptor_plan_compiles_exact_lens_path_into_relation_groups(tmp_path):
    with AccessMemoryLoop(tmp_path) as loop:
        atlas = loop.build_locality_atlas("atlas")
    plans = validate_dream_sculptor_plans("request", [plan(atlas)], [CAPTURE], atlas)
    assert plans[0].statement.context_refs == ("capture:capture-one",)
    assert plans[0].lenses[0].basis_spans[0].quote_utf8 == CAPTURE["user_utf8"]
    assert plans[0].relation_groups == (atlas.candidates[0].geometry_addresses,)
    assert plans[0].atlas_fingerprint == atlas.atlas_fingerprint
    assert "primary_candidate_id" not in plans[0].to_mapping()


def test_sculptor_plan_rejects_fabricated_span_unknown_path_and_free_primary(tmp_path):
    with AccessMemoryLoop(tmp_path) as loop:
        atlas = loop.build_locality_atlas("atlas")
    invalid = plan(atlas)
    invalid["lenses"][0]["basis_spans"][0]["quote_utf8"] = "东京晴天"
    with pytest.raises(ValueError, match="exact Capture"):
        validate_dream_sculptor_plans("request", [invalid], [CAPTURE], atlas)
    unknown = plan(atlas, ["invented"])
    with pytest.raises(ValueError, match="unknown"):
        validate_dream_sculptor_plans("request", [unknown], [CAPTURE], atlas)
    parallel_primary = {**plan(atlas), "primary_candidate_id": atlas.candidates[0].candidate_id}
    with pytest.raises(ValueError, match="fields"):
        validate_dream_sculptor_plans("request", [parallel_primary], [CAPTURE], atlas)


def test_lens_path_must_expose_leaf_and_lens_ablation_changes_geometry(tmp_path):
    with AccessMemoryLoop(tmp_path) as loop:
        first_atlas = loop.build_locality_atlas("empty")
        first = validate_dream_sculptor_plans("seed", [plan(first_atlas)], [CAPTURE], first_atlas)
        loop.apply_junction_plans(first, first_atlas, "seed-apply")
        atlas = loop.build_locality_atlas("occupied")
    resolved = validate_dream_sculptor_plans("resolved", [plan(atlas)], [CAPTURE], atlas)[0]
    unresolved = validate_dream_sculptor_plans("unresolved", [plan(atlas, unresolved=True, action="defer")], [CAPTURE], atlas)[0]
    assert resolved.relation_groups
    assert unresolved.relation_groups == ()


def test_lenses_are_operation_objects_not_atlas_or_core_state(tmp_path):
    with AccessMemoryLoop(tmp_path) as loop:
        atlas = loop.build_locality_atlas("atlas")
    assert isinstance(atlas, LocalityAtlas)
    wire = str(atlas.to_mapping()).lower()
    assert "future_query" not in wire and "lens_id" not in wire
    assert DREAM_SCULPTOR_SCHEMA_VERSION == "nollm_openclaw_dream_sculptor_v2"


def test_equivalent_resolved_lenses_reject_before_core(tmp_path):
    with AccessMemoryLoop(tmp_path) as loop:
        atlas = loop.build_locality_atlas("atlas")
    duplicate = plan(atlas)
    second = deepcopy(duplicate["lenses"][0])
    second["lens_id"] = "lens-weather"
    second["future_query"] = "东京天气如何？"
    duplicate["lenses"].append(second)
    with pytest.raises(ValueError, match="relation_groups must be unique"):
        validate_dream_sculptor_plans("request", [duplicate], [CAPTURE], atlas)
