import json

from nollm_core import CoreRuntime
from nollm_openclaw_formation.memory_loop import (
    PLACEMENT_SCHEMA_VERSION,
    build_placement_prompt,
    build_recall_prompt,
    apply_placement,
    render_recall_injection,
)


STATEMENT = {"statement_id": "dream:test", "content_utf8": "The release window is Wednesday at 3 PM.", "source_handle": None, "context_refs": []}
CELL = {"profile_id": "eisenstein_exact_v1", "chart_id": "default", "layer": 0, "q": 0, "r": 0, "phase": None}


def test_placement_uses_explicit_llm_geometry_and_persists_cursor(tmp_path):
    built = build_placement_prompt(STATEMENT, "agent:main:session-a", str(tmp_path), "placement-1")
    assert "local_geometry_context" in built["prompt"]
    applied = apply_placement(json.dumps({
        "schema_version": PLACEMENT_SCHEMA_VERSION,
        "outcome": "apply",
        "decision": {"statement_id": "dream:test", "action": "new", "target_cell": CELL, "reason_text": "explicit model placement"},
    }), STATEMENT, "agent:main:session-a", str(tmp_path), "placement-1")
    assert applied["outcome"] == "applied"
    assert applied["core_write_count"] == 1
    core = CoreRuntime(tmp_path)
    assert core.placement_count() == 1
    core.close()


def test_recall_is_bounded_to_cursor_and_rendered_as_hidden_context(tmp_path):
    test_placement_uses_explicit_llm_geometry_and_persists_cursor(tmp_path)
    built = build_recall_prompt("When is the release window?", "agent:main:session-a", str(tmp_path), "recall-1")
    assert built["available"] is True
    rendered = render_recall_injection(json.dumps({
        "schema_version": "nollm_openclaw_recall_v1", "outcome": "inject", "statement_ids": ["dream:test"],
    }), built["candidates"])
    assert rendered["outcome"] == "inject"
    assert "Wednesday" in rendered["injection"]


def test_new_session_uses_bounded_agent_cursor_after_reopen(tmp_path):
    test_placement_uses_explicit_llm_geometry_and_persists_cursor(tmp_path)
    reopened = build_recall_prompt("When is the release window?", "agent:main:new-session", str(tmp_path), "recall-cross-session")
    assert reopened["available"] is True
    assert reopened["cursor_source"] == "agent"
    assert len(reopened["entry_cells"]) == 1


def test_recall_without_cursor_is_none_without_global_discovery(tmp_path):
    built = build_recall_prompt("What do you remember?", "new-session", str(tmp_path), "recall-empty")
    assert built == {"available": False, "candidate_count": 0, "cursor_source": "agent"}


def test_failed_placement_leaves_no_new_statement_or_core_binding(tmp_path):
    invalid = {
        "schema_version": PLACEMENT_SCHEMA_VERSION,
        "outcome": "apply",
        "decision": {
            "statement_id": "dream:test",
            "action": "reuse",
            "existing_handle": {"geometry_address": CELL, "local_atom_id": "missing"},
            "reason_text": "missing explicit handle",
        },
    }
    try:
        apply_placement(json.dumps(invalid), STATEMENT, "agent:main:failure", str(tmp_path), "placement-failure")
    except Exception as exc:
        assert isinstance(exc, KeyError)
    else:
        raise AssertionError("invalid placement unexpectedly applied")
    assert not list((tmp_path / "access" / "statements").rglob("*.json"))
    core = CoreRuntime(tmp_path)
    assert core.placement_count() == 0
    core.close()


def test_placement_uses_the_same_limited_json_repair_rules(tmp_path):
    response = "JSON: " + json.dumps({
        "schema_version": PLACEMENT_SCHEMA_VERSION,
        "outcome": "apply",
        "decision": {"statement_id": "dream:test", "action": "new", "target_cell": CELL, "reason_text": "explicit model placement"},
    })
    applied = apply_placement(response, STATEMENT, "agent:main:repair", str(tmp_path), "placement-repair")
    assert applied["json_repair"]["repair_types"] == ["single_object_outer_text"]
