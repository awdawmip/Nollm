import json

import pytest

from nollm_access import AccessMemoryLoop, MemoryStatement
from nollm_openclaw_formation.adapter import FormationAdapterError
from nollm_openclaw_formation.sculptor import (
    apply_dream_sculptor_result,
    build_dream_sculptor_prompt,
    parse_dream_sculptor_result,
)


CAPTURES = [
    {
        "capture_id": "capture-tokyo",
        "user_utf8": "今天东京下雨了。",
        "assistant_utf8": "知道了。",
        "captured_epoch_ms": 1_768_582_400_000,
        "timezone_offset_minutes": 480,
    },
    {
        "capture_id": "capture-meeting",
        "user_utf8": "明天下午三点开会。",
        "assistant_utf8": "已记录。",
        "captured_epoch_ms": 1_768_582_400_000,
        "timezone_offset_minutes": 480,
    },
]


def _plan(draft_id, capture, content, atlas, candidate_id):
    quote = capture["user_utf8"]
    path = next(item for item in atlas["paths"] if candidate_id in item["leaf_locality_candidate_ids"])
    return {
        "draft_id": draft_id,
        "content_utf8": content,
        "source_capture_ids": [capture["capture_id"]],
        "lenses": [{
            "lens_id": f"lens-{draft_id}",
            "future_query": f"future query {draft_id}",
            "basis_spans": [{
                "capture_id": capture["capture_id"],
                "role": "user",
                "start": 0,
                "end": len(quote),
                "quote_utf8": quote,
            }],
            "atlas_path_ids": [path["path_id"]],
            "leaf_locality_candidate_ids": [candidate_id],
            "unresolved": False,
        }],
        "action": "expand_surface",
        "existing_handle": None,
        "reason_text": "complete proposition",
    }


def _wire(plans):
    return json.dumps({
        "schema_version": "nollm_openclaw_dream_sculptor_v2",
        "outcome": "plan",
        "plans": plans,
        "defer_reason": None,
    }, ensure_ascii=False)


def test_sculptor_prompt_teaches_complete_short_term_facts_and_geometry_boundary(tmp_path):
    built = build_dream_sculptor_prompt(CAPTURES, str(tmp_path), "prompt")
    prompt = built["prompt"]
    assert "Never filter" in prompt
    assert "user-grounded memory" in prompt
    assert "Python-style Unicode character indices" in prompt
    assert '"user_length_chars":8' in prompt
    assert "Weather, appointments, cancellations" in prompt
    assert "Never output q/r coordinates" in prompt
    assert "operation-local" in prompt
    assert "There is no separate primary/contact choice" in prompt
    assert "coverage_certificate covers every occupied physical Cell" in prompt
    assert built["schema_version"] == "nollm_openclaw_dream_sculptor_v2"
    assert built["atlas"]["schema_version"] == "nollm_access_locality_atlas_v3"
    assert built["atlas"]["coverage_certificate"]["uncovered_field_cell_count"] == 0


def test_sculptor_returns_retryable_overflow_without_a_provider_prompt(tmp_path):
    entry = None
    with AccessMemoryLoop(tmp_path) as loop:
        for index in range(40):
            candidate = next(
                item for item in loop.placement_candidates(entry, f"seed:{index}")
                if item["relation_kind"] == "expand_surface"
            )
            result = loop.apply_placement(
                MemoryStatement(f"atom-{index}", str(index)),
                {
                    "schema_version": "nollm_openclaw_surface_placement_v1",
                    "outcome": "apply",
                    "decision": {
                        "statement_id": f"atom-{index}",
                        "action": "expand_surface",
                        "candidate_id": candidate["candidate_id"],
                        "reason_text": "bounded overflow fixture",
                    },
                },
                f"seed:{index}",
                entry,
            )
            entry = result["handle"]["geometry_address"]
    built = build_dream_sculptor_prompt(CAPTURES[:1], str(tmp_path), "overflow", candidate_limit=8)
    assert built["status"] == "atlas_overflow"
    assert built["retryable"] is True
    assert "prompt" not in built
    assert built["atlas"]["coverage_certificate"] == {
        "occupied_field_cell_count": 40,
        "covered_field_cell_count": 0,
        "uncovered_field_cell_count": 40,
        "selected_aggregation_order": None,
        "region_count": 0,
        "overflow": True,
        "order_projection_counts": built["atlas"]["coverage_certificate"]["order_projection_counts"],
    }


def test_one_sculptor_result_applies_two_capture_bound_statements_via_core_junction(tmp_path):
    built = build_dream_sculptor_prompt(CAPTURES, str(tmp_path), "batch")
    candidate = built["atlas"]["candidates"][0]["candidate_id"]
    raw = _wire([
        _plan("d1", CAPTURES[0], "2026年1月17日东京下雨了。", built["atlas"], candidate),
        _plan("d2", CAPTURES[1], "2026年1月18日下午三点开会。", built["atlas"], candidate),
    ])
    parsed = parse_dream_sculptor_result(raw, CAPTURES, built["atlas"], "batch")
    assert [item["source_capture_ids"] for item in parsed["plans"]] == [["capture-tokyo"], ["capture-meeting"]]
    applied = apply_dream_sculptor_result(raw, CAPTURES, built["atlas"], str(tmp_path), "batch")
    assert [item["outcome"] for item in applied["outcomes"]] == ["applied", "applied"]
    assert all(item["durable_commit"]["reopen_verified"] for item in applied["outcomes"])
    assert applied["outcomes"][0]["junction"]["cell"] != applied["outcomes"][1]["junction"]["cell"]
    with AccessMemoryLoop(tmp_path) as loop:
        assert all(loop.binding(item["statement_id"])["current_statement_id"] == item["statement_id"] for item in applied["outcomes"])
    durable_text = "\n".join(path.read_text("utf-8") for path in tmp_path.rglob("*.json"))
    assert "future query" not in durable_text
    assert "lens-d" not in durable_text


def test_sculptor_rejects_stale_atlas_before_any_plan_write(tmp_path):
    built = build_dream_sculptor_prompt(CAPTURES[:1], str(tmp_path), "stale")
    candidate = built["atlas"]["candidates"][0]["candidate_id"]
    raw = _wire([_plan("d1", CAPTURES[0], "2026年1月17日东京下雨了。", built["atlas"], candidate)])
    with AccessMemoryLoop(tmp_path) as loop:
        atlas = loop.build_locality_atlas("mutation")
        mutation = _wire([_plan("d1", CAPTURES[0], "unrelated mutation", atlas.to_mapping(), atlas.candidates[0].candidate_id)])
    apply_dream_sculptor_result(mutation, CAPTURES[:1], atlas.to_mapping(), str(tmp_path), "mutation")
    with pytest.raises(ValueError, match="Atlas changed"):
        apply_dream_sculptor_result(raw, CAPTURES[:1], built["atlas"], str(tmp_path), "stale")


def test_sculptor_revision_requires_bound_confirmation_and_keeps_one_handle(tmp_path):
    built = build_dream_sculptor_prompt(CAPTURES[:1], str(tmp_path), "initial")
    candidate = built["atlas"]["candidates"][0]["candidate_id"]
    initial_raw = _wire([_plan("d1", CAPTURES[0], "Tokyo weather is rainy.", built["atlas"], candidate)])
    initial = apply_dream_sculptor_result(initial_raw, CAPTURES[:1], built["atlas"], str(tmp_path), "initial")
    handle = initial["outcomes"][0]["durable_commit"]["handle"]

    revision_capture = [{**CAPTURES[0], "capture_id": "capture-revision", "user_utf8": "Correction: Tokyo weather is sunny."}]
    revision_built = build_dream_sculptor_prompt(revision_capture, str(tmp_path), "revision")
    occupied = next(item for item in revision_built["atlas"]["candidates"] if item["occupied"])
    revision_plan = _plan("d1", revision_capture[0], "Tokyo weather is sunny.", revision_built["atlas"], occupied["candidate_id"])
    revision_plan.update({
        "action": "revision_current",
        "existing_handle": handle,
    })
    revision_raw = _wire([revision_plan])
    provisional_result = apply_dream_sculptor_result(
        revision_raw, revision_capture, revision_built["atlas"], str(tmp_path), "revision",
    )
    provisional = provisional_result["outcomes"][0]
    assert provisional["outcome"] == "revision_confirmation_required"
    with AccessMemoryLoop(tmp_path) as loop:
        assert loop.binding(initial["outcomes"][0]["statement_id"])["current_statement_id"] == initial["outcomes"][0]["statement_id"]

    confirmation = {
        "schema_version": "nollm_openclaw_revision_confirmation_v1",
        "provisional_id": provisional["provisional_revision"]["provisional_id"],
        "outcome": "confirm_revision",
        "relation": "same_subject_same_slot_supersedes",
    }
    statement_id = provisional["statement_id"]
    applied = apply_dream_sculptor_result(
        revision_raw, revision_capture, revision_built["atlas"], str(tmp_path), "revision",
        {statement_id: confirmation}, [statement_id],
    )
    assert applied["outcomes"][0]["outcome"] == "applied"
    assert applied["outcomes"][0]["durable_commit"]["handle"] == handle
    with AccessMemoryLoop(tmp_path) as loop:
        assert loop.binding(statement_id)["current_statement_id"] == statement_id
