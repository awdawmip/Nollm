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
    built = build_placement_prompt(STATEMENT, "session-a", str(tmp_path), "placement-1")
    assert "local_geometry_context" in built["prompt"]
    applied = apply_placement(json.dumps({
        "schema_version": PLACEMENT_SCHEMA_VERSION,
        "outcome": "apply",
        "decision": {"statement_id": "dream:test", "action": "new", "target_cell": CELL, "reason_text": "explicit model placement"},
    }), STATEMENT, "session-a", str(tmp_path), "placement-1")
    assert applied["outcome"] == "applied"
    assert applied["core_write_count"] == 1
    core = CoreRuntime(tmp_path)
    assert core.placement_count() == 1
    core.close()


def test_recall_is_bounded_to_cursor_and_rendered_as_hidden_context(tmp_path):
    test_placement_uses_explicit_llm_geometry_and_persists_cursor(tmp_path)
    built = build_recall_prompt("When is the release window?", "session-a", str(tmp_path), "recall-1")
    assert built["available"] is True
    rendered = render_recall_injection(json.dumps({
        "schema_version": "nollm_openclaw_recall_v1", "outcome": "inject", "statement_ids": ["dream:test"],
    }), built["candidates"])
    assert rendered["outcome"] == "inject"
    assert "Wednesday" in rendered["injection"]


def test_recall_without_cursor_is_none_without_global_discovery(tmp_path):
    built = build_recall_prompt("What do you remember?", "new-session", str(tmp_path), "recall-empty")
    assert built == {"available": False, "candidate_count": 0}
