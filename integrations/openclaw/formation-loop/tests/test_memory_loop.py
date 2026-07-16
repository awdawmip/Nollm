import json

import pytest

from nollm_access import AccessMemoryLoop, MemoryStatement
from nollm_openclaw_formation.adapter import FormationAdapterError
from nollm_openclaw_formation.memory_loop import (
    PLACEMENT_SCHEMA_VERSION,
    RECALL_SCHEMA_VERSION,
    TRAVERSAL_SCHEMA_VERSION,
    advance_placement_traversal,
    advance_recall_traversal,
    apply_placement,
    build_placement_prompt,
    build_recall_prompt,
    render_recall_injection,
)


STATEMENT = {"statement_id": "dream:test", "content_utf8": "The release window is Wednesday at 3 PM.", "source_handle": None, "context_refs": []}
CELL = {"profile_id": "default_dream_v1", "chart_id": "default", "layer": 0, "q": 0, "r": 0, "phase": None}


def placement(statement_id: str, action: str, candidate_id: str) -> str:
    return json.dumps({
        "schema_version": PLACEMENT_SCHEMA_VERSION,
        "outcome": "apply",
        "decision": {"statement_id": statement_id, "action": action, "candidate_id": candidate_id, "reason_text": "model selected finite candidate"},
    })


def navigation(action: str, candidate_id: str | None = None) -> str:
    value = {"schema_version": TRAVERSAL_SCHEMA_VERSION, "action": action}
    if candidate_id is not None:
        value["candidate_id"] = candidate_id
    return json.dumps(value)


def place_initial(workspace) -> dict[str, object]:
    built = build_placement_prompt(STATEMENT, str(workspace), "placement-1")
    assert built["status"] == "placement_decision"
    candidate = built["candidates"][0]
    applied = apply_placement(
        placement("dream:test", "expand_surface", candidate["candidate_id"]),
        STATEMENT,
        str(workspace),
        "placement-1",
        built["selected_entry"],
    )
    return applied


def test_empty_surface_placement_expands_without_persistent_entry_hint(tmp_path):
    applied = place_initial(tmp_path)
    assert applied["outcome"] == "applied"
    assert applied["action"] == "expand_surface"
    assert applied["handle"]["geometry_address"] == CELL
    assert not (tmp_path / "openclaw" / "memory_cursor.json").exists()
    with AccessMemoryLoop(tmp_path) as loop:
        assert loop.binding("dream:test")["current_statement_id"] == "dream:test"


def test_recall_traverses_surface_then_renders_hidden_context(tmp_path):
    place_initial(tmp_path)
    built = build_recall_prompt("When is the release window?", str(tmp_path), "recall-1")
    assert built["status"] == "traverse"
    candidate = built["surface"]["surface_cells"][0]["candidate_id"]
    physical = advance_recall_traversal(
        "When is the release window?",
        built["traversal_state"],
        navigation("open_physical_entries", candidate),
        str(tmp_path),
    )
    recalled = physical
    assert recalled["status"] == "recall_decision"
    assert recalled["entry_cell"] == CELL
    assert recalled["resolved_singleton"] is True
    assert set(recalled["core_recall"]) == {"budget_exhausted"}
    assert set(recalled["operation_timing"]) == {"physical_entry_resolution_ms", "physical_entry_model_call_skipped", "recall_core_ms"}
    assert recalled["operation_timing"]["physical_entry_model_call_skipped"] is True
    assert recalled["physical_entry_model_call_skipped"] is True
    assert recalled["resolution_policy_id"] == "mechanical_singleton_physical_entry_v1"
    assert "entry_cells" not in recalled
    assert "per_entry_core_recall" not in recalled
    assert recalled["candidates"][0]["path"] == []
    assert recalled["candidates"][0]["path_is_not_truth_proof"] is True
    rendered = render_recall_injection(json.dumps({
        "schema_version": RECALL_SCHEMA_VERSION,
        "outcome": "inject",
        "statement_ids": ["dream:test"],
    }), recalled["candidates"])
    assert rendered["outcome"] == "inject"
    assert "Wednesday" in rendered["injection"]


def test_fresh_operation_reopens_from_surface_without_prior_operation_state(tmp_path):
    place_initial(tmp_path)
    first = build_recall_prompt("release", str(tmp_path), "recall:first")
    second = build_recall_prompt("release", str(tmp_path), "recall:fresh")
    assert first["surface"]["active_order"] == second["surface"]["active_order"]
    assert first["traversal_state"]["after"] is None
    assert second["traversal_state"]["after"] is None
    assert "session" not in json.dumps(second["traversal_state"]).lower()


def test_forced_coarse_surface_uses_coverage_descent(tmp_path):
    place_initial(tmp_path)
    budget = {
        "page_size": 8, "max_pages": 1, "max_surface_cells": 1,
        "page_overhead_units": 8, "cell_preview_units": 4,
        "max_projection_units": 1,
        "max_descent_depth": 8, "hard_max_order": 8, "max_calls": 24,
    }
    result = build_recall_prompt("release", str(tmp_path), "recall:coarse", budget)
    assert result["surface"]["active_order"] == 8
    assert result["surface"]["overflow"] is True
    assert "return_to_parent" not in result["surface"]["legal_actions"]
    assert "request_coarser_surface" not in result["surface"]["legal_actions"]
    assert '"action":"return_to_parent"' not in result["prompt"]
    assert '"action":"request_coarser_surface"' not in result["prompt"]
    assert '"action":"open_surface_cell"' in result["prompt"]
    assert '"action":"open_physical_entries"' not in result["prompt"]
    for expected_order in range(7, -1, -1):
        candidate = result["surface"]["surface_cells"][0]["candidate_id"]
        result = advance_recall_traversal("release", result["traversal_state"], navigation("open_surface_cell", candidate), str(tmp_path))
        assert result["surface"]["current_order"] == expected_order
    assert '"action":"open_physical_entries"' in result["prompt"]
    assert '"action":"open_surface_cell"' not in result["prompt"]
    assert "open_physical_entries" in result["surface"]["legal_actions"]
    candidate = result["surface"]["surface_cells"][0]["candidate_id"]
    result = advance_recall_traversal("release", result["traversal_state"], navigation("open_physical_entries", candidate), str(tmp_path))
    assert result["status"] == "recall_decision"


def test_unshown_candidate_and_malformed_navigation_do_not_execute(tmp_path):
    place_initial(tmp_path)
    built = build_recall_prompt("release", str(tmp_path), "recall:invalid")
    with pytest.raises(FormationAdapterError, match="unavailable"):
        advance_recall_traversal("release", built["traversal_state"], navigation("open_physical_entries", "surface:invented"), str(tmp_path))
    surface_candidate = built["surface"]["surface_cells"][0]["candidate_id"]
    with pytest.raises(FormationAdapterError, match="not legal for the current page"):
        advance_recall_traversal("release", built["traversal_state"], navigation("select_entry", surface_candidate), str(tmp_path))
    physical = advance_recall_traversal("release", built["traversal_state"], navigation("open_physical_entries", surface_candidate), str(tmp_path))
    assert physical["physical_entry_model_call_skipped"] is True
    with pytest.raises(FormationAdapterError, match="fields"):
        advance_recall_traversal("release", built["traversal_state"], json.dumps({"schema_version": TRAVERSAL_SCHEMA_VERSION, "action": "none", "candidate_id": "x"}), str(tmp_path))


def test_recall_rejects_multi_entry_and_propagates_from_one_entry(tmp_path):
    place_initial(tmp_path)
    second = {"statement_id": "dream:second", "content_utf8": "The risk review is Tuesday.", "source_handle": None, "context_refs": []}
    with AccessMemoryLoop(tmp_path) as loop:
        loop.apply_placement(
            MemoryStatement.from_mapping(second),
            json.loads(placement("dream:second", "new_local", "placement:lateral:0")),
            "placement-2",
            CELL,
        )
    built = build_recall_prompt("release", str(tmp_path), "recall:multi")
    shown = [item["candidate_id"] for item in built["surface"]["surface_cells"]]
    invalid_multi = json.dumps({
        "schema_version": TRAVERSAL_SCHEMA_VERSION,
        "action": "select_entries",
        "candidate_ids": shown,
    })
    with pytest.raises(FormationAdapterError, match="fields"):
        advance_recall_traversal("release", built["traversal_state"], invalid_multi, str(tmp_path))
    physical = advance_recall_traversal(
        "release", built["traversal_state"], navigation("open_physical_entries", shown[0]), str(tmp_path)
    )
    recalled = physical
    assert recalled["entry_cell"]["profile_id"] == "default_dream_v1"
    assert {item["statement_id"] for item in recalled["candidates"]} == {"dream:test", "dream:second"}


def test_none_and_failed_placement_leave_no_pollution(tmp_path):
    assert build_recall_prompt("What do you remember?", str(tmp_path), "recall-empty")["status"] == "complete_none"
    built = build_placement_prompt(STATEMENT, str(tmp_path), "placement-failure")
    with pytest.raises(FormationAdapterError, match="unavailable candidate"):
        apply_placement(placement("dream:test", "expand_surface", "outside:99"), STATEMENT, str(tmp_path), "placement-failure", built["selected_entry"])
    assert not list((tmp_path / "access" / "statements").rglob("*.json"))
    assert not (tmp_path / "openclaw" / "memory_cursor.json").exists()


def test_malformed_existing_handle_is_retryable_schema_failure_without_orphan(tmp_path):
    place_initial(tmp_path)
    second = {"statement_id": "dream:malformed", "content_utf8": "Malformed placement must not persist.", "source_handle": None, "context_refs": []}
    built = build_placement_prompt(second, str(tmp_path), "placement-malformed")
    surface_candidate = built["surface"]["surface_cells"][0]["candidate_id"]
    physical = advance_placement_traversal(
        second,
        built["traversal_state"],
        navigation("open_physical_entries", surface_candidate),
        str(tmp_path),
    )
    built = physical
    assert built["physical_entry_model_call_skipped"] is True
    candidate = built["candidates"][0]
    raw = json.dumps({
        "schema_version": PLACEMENT_SCHEMA_VERSION,
        "outcome": "apply",
        "decision": {
            "statement_id": "dream:malformed",
            "action": "reuse",
            "candidate_id": candidate["candidate_id"],
            "existing_handle": "not-an-atom-handle",
            "reason_text": "malformed model output",
        },
    })
    with pytest.raises(FormationAdapterError) as error:
        apply_placement(raw, second, str(tmp_path), "placement-malformed", built["selected_entry"])
    assert error.value.category == "invalid_schema"
    with AccessMemoryLoop(tmp_path) as loop:
        with pytest.raises(KeyError):
            loop.binding("dream:malformed")


def test_placement_uses_limited_json_repair(tmp_path):
    built = build_placement_prompt(STATEMENT, str(tmp_path), "placement-repair")
    response = "JSON: " + placement("dream:test", "expand_surface", built["candidates"][0]["candidate_id"])
    applied = apply_placement(response, STATEMENT, str(tmp_path), "placement-repair", None)
    assert applied["json_repair"]["repair_types"] == ["single_object_outer_text"]


def test_placement_prompt_defines_strict_revision_boundaries(tmp_path):
    built = build_placement_prompt(STATEMENT, str(tmp_path), "placement-semantics")
    prompt = built["prompt"]
    assert "nollm_access_semantic_placement_actions_v1" in prompt
    assert "same subject or referent" in prompt
    assert "same proposition slot" in prompt
    assert "explicitly supersedes" in prompt
    assert "Different subjects with analogous attributes must remain distinct" in prompt
    assert "An additive fact about the same subject is not a revision" in prompt
