import pytest

from nollm_access import AccessMemoryLoop, DREAM_SCULPTOR_SCHEMA_VERSION, LocalityAtlas, validate_dream_sculptor_plans


CAPTURE = {
    "capture_id": "capture-one",
    "user_utf8": "今天东京下雨了。",
    "assistant_utf8": "知道了。",
    "captured_epoch_ms": 1_784_275_200_000,
    "timezone_offset_minutes": 480,
}


def plan(candidate_id):
    return {
        "draft_id": "d1",
        "content_utf8": "2026年7月17日东京下雨了。",
        "source_capture_ids": ["capture-one"],
        "lenses": [{
            "lens_id": "lens-date",
            "future_query": "2026年7月17日发生了什么？",
            "basis_spans": [{"capture_id": "capture-one", "role": "user", "start": 0, "end": 8, "quote_utf8": "今天东京下雨了。"}],
            "locality_candidate_ids": [candidate_id],
            "unresolved": False,
        }],
        "action": "expand_surface",
        "primary_candidate_id": candidate_id,
        "contact_candidate_ids": [],
        "existing_handle": None,
        "reason_text": "new complete proposition",
    }


def test_sculptor_plan_validates_exact_basis_and_generates_capture_bound_statement(tmp_path):
    with AccessMemoryLoop(tmp_path) as loop:
        atlas = loop.build_locality_atlas("atlas")
    plans = validate_dream_sculptor_plans("request", [plan(atlas.candidates[0].candidate_id)], [CAPTURE], atlas)
    assert len(plans) == 1
    assert plans[0].statement.context_refs == ("capture:capture-one",)
    assert plans[0].lenses[0].basis_spans[0].quote_utf8 == CAPTURE["user_utf8"]
    assert plans[0].to_mapping()["lenses"][0]["future_query"] == "2026年7月17日发生了什么？"


def test_sculptor_plan_rejects_fabricated_span_candidate_and_coordinates(tmp_path):
    with AccessMemoryLoop(tmp_path) as loop:
        atlas = loop.build_locality_atlas("atlas")
    invalid = plan(atlas.candidates[0].candidate_id)
    invalid["lenses"][0]["basis_spans"][0]["quote_utf8"] = "东京晴天"
    with pytest.raises(ValueError, match="exact Capture"):
        validate_dream_sculptor_plans("request", [invalid], [CAPTURE], atlas)
    unknown = plan("invented")
    with pytest.raises(ValueError, match="unknown"):
        validate_dream_sculptor_plans("request", [unknown], [CAPTURE], atlas)
    coordinate = {**plan(atlas.candidates[0].candidate_id), "q": 1}
    with pytest.raises(ValueError, match="fields"):
        validate_dream_sculptor_plans("request", [coordinate], [CAPTURE], atlas)


def test_lenses_are_operation_objects_not_atlas_or_core_state(tmp_path):
    with AccessMemoryLoop(tmp_path) as loop:
        atlas = loop.build_locality_atlas("atlas")
    assert isinstance(atlas, LocalityAtlas)
    wire = str(atlas.to_mapping()).lower()
    assert "future_query" not in wire
    assert "lens_id" not in wire
    assert DREAM_SCULPTOR_SCHEMA_VERSION == "nollm_openclaw_dream_sculptor_v1"
