import json

import pytest

from nollm_access import AccessMemoryLoop
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
CELL = {"profile_id": "eisenstein_exact_v1", "chart_id": "default", "layer": 0, "q": 0, "r": 0, "phase": None}


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
    recalled = advance_recall_traversal(
        "When is the release window?",
        built["traversal_state"],
        navigation("select_entry", candidate),
        str(tmp_path),
    )
    assert recalled["status"] == "recall_decision"
    assert len(recalled["per_entry_core_recall"]) == 1
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
        "max_projection_units": 1, "selected_entries_limit": 3,
        "max_descent_depth": 2, "hard_max_order": 2, "max_calls": 12,
    }
    result = build_recall_prompt("release", str(tmp_path), "recall:coarse", budget)
    assert result["surface"]["active_order"] == 2
    assert result["surface"]["overflow"] is True
    for expected_order in (1, 0):
        candidate = result["surface"]["surface_cells"][0]["candidate_id"]
        result = advance_recall_traversal("release", result["traversal_state"], navigation("open_surface_cell", candidate), str(tmp_path))
        assert result["surface"]["current_order"] == expected_order
    candidate = result["surface"]["surface_cells"][0]["candidate_id"]
    result = advance_recall_traversal("release", result["traversal_state"], navigation("select_entry", candidate), str(tmp_path))
    assert result["status"] == "recall_decision"


def test_unshown_candidate_and_malformed_navigation_do_not_execute(tmp_path):
    place_initial(tmp_path)
    built = build_recall_prompt("release", str(tmp_path), "recall:invalid")
    with pytest.raises(FormationAdapterError, match="unavailable"):
        advance_recall_traversal("release", built["traversal_state"], navigation("select_entry", "surface:invented"), str(tmp_path))
    with pytest.raises(FormationAdapterError, match="fields"):
        advance_recall_traversal("release", built["traversal_state"], json.dumps({"schema_version": TRAVERSAL_SCHEMA_VERSION, "action": "none", "candidate_id": "x"}), str(tmp_path))


def test_none_and_failed_placement_leave_no_pollution(tmp_path):
    assert build_recall_prompt("What do you remember?", str(tmp_path), "recall-empty")["status"] == "complete_none"
    built = build_placement_prompt(STATEMENT, str(tmp_path), "placement-failure")
    with pytest.raises(ValueError, match="unavailable candidate"):
        apply_placement(placement("dream:test", "expand_surface", "outside:99"), STATEMENT, str(tmp_path), "placement-failure", built["selected_entry"])
    assert not list((tmp_path / "access" / "statements").rglob("*.json"))
    assert not (tmp_path / "openclaw" / "memory_cursor.json").exists()


def test_placement_uses_limited_json_repair(tmp_path):
    built = build_placement_prompt(STATEMENT, str(tmp_path), "placement-repair")
    response = "JSON: " + placement("dream:test", "expand_surface", built["candidates"][0]["candidate_id"])
    applied = apply_placement(response, STATEMENT, str(tmp_path), "placement-repair", None)
    assert applied["json_repair"]["repair_types"] == ["single_object_outer_text"]
