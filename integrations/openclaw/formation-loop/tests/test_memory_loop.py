import json

import pytest

from nollm_access import AccessMemoryLoop
from nollm_openclaw_formation.memory_loop import (
    PLACEMENT_SCHEMA_VERSION,
    apply_placement,
    build_placement_prompt,
    build_recall_prompt,
    render_recall_injection,
)


STATEMENT = {"statement_id": "dream:test", "content_utf8": "The release window is Wednesday at 3 PM.", "source_handle": None, "context_refs": []}
CELL = {"profile_id": "eisenstein_exact_v1", "chart_id": "default", "layer": 0, "q": 0, "r": 0, "phase": None}


def _new(statement_id: str, action: str, candidate_id: str) -> str:
    return json.dumps({
        "schema_version": PLACEMENT_SCHEMA_VERSION,
        "outcome": "apply",
        "decision": {"statement_id": statement_id, "action": action, "candidate_id": candidate_id, "reason_text": "model selected finite candidate"},
    })


def test_placement_uses_access_candidate_and_persists_bounded_cursor(tmp_path):
    built = build_placement_prompt(STATEMENT, "agent:main:session-a", str(tmp_path), "placement-1")
    assert "finite_geometry_candidates" in built["prompt"]
    assert built["candidates"][0]["candidate_id"] == "new_cluster:0"
    applied = apply_placement(_new("dream:test", "new_cluster", "new_cluster:0"), STATEMENT, "agent:main:session-a", str(tmp_path), "placement-1")
    assert applied["outcome"] == "applied"
    assert applied["action"] == "new_cluster"
    assert applied["handle"]["geometry_address"] == CELL
    assert applied["cursor"] == {"cluster_anchors": [CELL], "entry_cells": [CELL]}
    with AccessMemoryLoop(tmp_path) as loop:
        assert loop.binding("dream:test")["current_statement_id"] == "dream:test"


def test_recall_is_per_anchor_and_rendered_as_hidden_context(tmp_path):
    test_placement_uses_access_candidate_and_persists_bounded_cursor(tmp_path)
    built = build_recall_prompt("When is the release window?", "agent:main:session-a", str(tmp_path), "recall-1")
    assert built["available"] is True
    assert len(built["per_anchor_core_recall"]) == 1
    rendered = render_recall_injection(json.dumps({
        "schema_version": "nollm_openclaw_recall_v1", "outcome": "inject", "statement_ids": ["dream:test"],
    }), built["candidates"])
    assert rendered["outcome"] == "inject"
    assert "Wednesday" in rendered["injection"]


def test_new_session_uses_bounded_agent_anchors_after_reopen(tmp_path):
    test_placement_uses_access_candidate_and_persists_bounded_cursor(tmp_path)
    reopened = build_recall_prompt("When is the release window?", "agent:main:new-session", str(tmp_path), "recall-cross-session")
    assert reopened["available"] is True
    assert reopened["cursor_source"] == "agent"
    assert reopened["cluster_anchors"] == [CELL]


def test_new_session_placement_receives_only_finite_agent_candidates(tmp_path):
    test_placement_uses_access_candidate_and_persists_bounded_cursor(tmp_path)
    built = build_placement_prompt(
        {**STATEMENT, "statement_id": "dream:revision", "content_utf8": "The release window moved to Thursday at 4 PM."},
        "agent:main:new-session", str(tmp_path), "placement-cross-session",
    )
    assert len(built["candidates"]) == 8
    assert sum(item["relation_kind"] == "lateral_ring_1" for item in built["candidates"]) == 6
    assert "dream:test" in built["prompt"]
    assert '"candidate_id":"existing_cell:0"' in built["prompt"]
    assert "Never return target_cell" in built["prompt"]


def test_recall_without_anchor_is_none_without_global_discovery(tmp_path):
    built = build_recall_prompt("What do you remember?", "new-session", str(tmp_path), "recall-empty")
    assert built == {"available": False, "candidate_count": 0, "cursor_source": "agent"}


def test_failed_candidate_does_not_write_statement_or_cursor(tmp_path):
    invalid = _new("dream:test", "new_cluster", "outside:99")
    with pytest.raises(ValueError, match="unavailable candidate"):
        apply_placement(invalid, STATEMENT, "agent:main:failure", str(tmp_path), "placement-failure")
    assert not list((tmp_path / "access" / "statements").rglob("*.json"))
    assert not (tmp_path / "openclaw" / "memory_cursor.json").exists()


def test_llm_cannot_supply_candidate_outside_address(tmp_path):
    value = json.loads(_new("dream:test", "new_cluster", "new_cluster:0"))
    value["decision"]["target_cell"] = CELL
    with pytest.raises(ValueError, match="unrelated fields"):
        apply_placement(json.dumps(value), STATEMENT, "agent:main:outside", str(tmp_path), "placement-outside")


def test_placement_uses_the_same_limited_json_repair_rules(tmp_path):
    response = "JSON: " + _new("dream:test", "new_cluster", "new_cluster:0")
    applied = apply_placement(response, STATEMENT, "agent:main:repair", str(tmp_path), "placement-repair")
    assert applied["json_repair"]["repair_types"] == ["single_object_outer_text"]
