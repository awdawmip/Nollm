import json

import pytest

from nollm_access import AccessMemoryLoop, AccessRuntime, MemoryStatement
from nollm_core import CoreRuntime, GeometryAddress, MemoryAtom
from nollm_openclaw_formation.adapter import FormationAdapterError
from nollm_openclaw_formation.memory_loop import (
    PLACEMENT_SCHEMA_VERSION,
    RECALL_SCHEMA_VERSION,
    TRAVERSAL_SCHEMA_VERSION,
    FAST_RECALL_SCHEMA_VERSION,
    BATCH_PLACEMENT_SCHEMA_VERSION,
    advance_placement_traversal,
    advance_recall_traversal,
    apply_placement,
    build_placement_prompt,
    build_recall_prompt,
    build_revision_confirmation_prompt,
    build_revision_redecision_prompt,
    parse_revision_confirmation,
    render_recall_injection,
    build_fast_recall_prompt,
    apply_fast_recall_selection,
    build_batch_placement_prompt,
    apply_batch_placement,
    verify_admitted_statements,
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


def test_fast_recall_mechanical_singleton_uses_zero_hidden_calls(tmp_path):
    place_initial(tmp_path)
    recalled = build_fast_recall_prompt("When is the release window?", str(tmp_path), "fast-single")
    assert recalled["status"] == "complete_inject"
    assert recalled["hidden_call_count"] == 0
    assert recalled["selected_entry"] == CELL
    assert recalled["statement_ids"] == ["dream:test"]
    assert "Wednesday" in recalled["injection"]


def test_fast_recall_selects_one_geometry_entry_then_injects_without_second_selection(tmp_path):
    place_initial(tmp_path)
    second = {"statement_id": "dream:second", "content_utf8": "The deployment color is green.", "source_handle": None, "context_refs": []}
    built = build_placement_prompt(second, str(tmp_path), "placement-second")
    while built["status"] == "traverse":
        candidate = built["surface"]["surface_cells"][0]["candidate_id"]
        built = advance_placement_traversal(second, built["traversal_state"], navigation("open_physical_entries", candidate), str(tmp_path))
    if built["status"] == "physical_entry":
        built = advance_placement_traversal(second, built["traversal_state"], navigation("defer"), str(tmp_path))
    if built["status"] != "placement_decision":
        built = build_placement_prompt(second, str(tmp_path), "placement-second-frontier")
        # Select no existing locality: the bounded fallback remains the explicit frontier.
        with AccessMemoryLoop(tmp_path) as loop:
            candidates = loop.placement_candidates(None, "placement-second-frontier:candidates")
        applied = apply_placement(placement("dream:second", "expand_surface", candidates[0]["candidate_id"]), second, str(tmp_path), "placement-second-frontier", None)
    else:
        frontier = next(item for item in built["candidates"] if item["relation_kind"] == "expand_surface")
        applied = apply_placement(placement("dream:second", "expand_surface", frontier["candidate_id"]), second, str(tmp_path), "placement-second", built["selected_entry"])
    assert applied["outcome"] == "applied"
    decision = build_fast_recall_prompt("What is the release window?", str(tmp_path), "fast-many")
    assert decision["status"] == "entry_decision"
    chosen = next(item for item in decision["entries"] if any(statement["statement_id"] == "dream:test" for statement in item["statements"]))
    result = apply_fast_recall_selection(json.dumps({"schema_version": FAST_RECALL_SCHEMA_VERSION, "outcome": "select", "entry_id": chosen["entry_id"]}), decision["entries"], str(tmp_path), "fast-many")
    assert result["hidden_call_count"] == 1
    assert result["status"] == "complete_inject"
    assert "dream:test" in result["statement_ids"]


@pytest.mark.parametrize("count,target_q", [(40, 39), (300, 299), (1027, 1026)])
def test_fast_recall_uses_complete_progressive_atlas_not_stable_prefix(tmp_path, count, target_q):
    with CoreRuntime(tmp_path) as core:
        for q in range(count):
            core.put(MemoryAtom(f"atom-{q}", str(q)), GeometryAddress("default_dream_v1", "default", 0, q, 0))
    built = build_fast_recall_prompt(f"Find target {target_q}", str(tmp_path), f"large-{count}")

    assert built["status"] == "entry_decision"
    assert built["hidden_call_count"] == 1
    assert built["prompt_utf8_bytes"] <= 65536
    assert built["atlas_page"]["coverage_certificate"]["occupied_field_cell_count"] == count
    assert built["atlas_page"]["coverage_certificate"]["uncovered_source_cell_count"] == 0
    assert len(built["atlas_page"]["regions"]) <= 32
    assert any(entry["entry_cell"]["q"] == target_q for entry in built["entries"])


def test_batch_placement_uses_one_frozen_geometry_view_and_durable_atomic_apply(tmp_path):
    statements = [
        STATEMENT,
        {"statement_id": "dream:second", "content_utf8": "The deployment color is green.", "source_handle": None, "context_refs": []},
    ]
    built = build_batch_placement_prompt(statements, str(tmp_path), "batch-one")
    empty = [item for item in built["candidates"] if item["occupancy"]["count"] == 0]
    decisions = [
        {"statement_id": statement["statement_id"], "outcome": "apply", "action": "expand_surface", "candidate_id": empty[index]["candidate_id"], "reason_text": "distinct durable fact"}
        for index, statement in enumerate(statements)
    ]
    applied = apply_batch_placement(
        json.dumps({"schema_version": BATCH_PLACEMENT_SCHEMA_VERSION, "decisions": decisions}),
        statements, str(tmp_path), "batch-one", built["view_fingerprint"],
    )
    assert [item["outcome"] for item in applied["outcomes"]] == ["applied", "applied"]
    assert all(item["durable_commit"]["reopen_verified"] for item in applied["outcomes"])
    with AccessMemoryLoop(tmp_path) as loop:
        assert loop.binding("dream:test")["current_statement_id"] == "dream:test"
        assert loop.binding("dream:second")["current_statement_id"] == "dream:second"
    assert verify_admitted_statements(["dream:test", "dream:second"], str(tmp_path)) == {
        "status": "verified",
        "statement_ids": ["dream:test", "dream:second"],
        "reopen_verified": True,
    }


def test_batch_placement_rejects_stale_view_before_any_write(tmp_path):
    built = build_batch_placement_prompt([STATEMENT], str(tmp_path), "batch-stale")
    place_initial(tmp_path)
    decision = {"statement_id": "dream:test", "outcome": "apply", "action": "expand_surface", "candidate_id": built["candidates"][0]["candidate_id"], "reason_text": "stale"}
    with pytest.raises(FormationAdapterError, match="view changed"):
        apply_batch_placement(json.dumps({"schema_version": BATCH_PLACEMENT_SCHEMA_VERSION, "decisions": [decision]}), [STATEMENT], str(tmp_path), "batch-stale", built["view_fingerprint"])


def test_batch_placement_commits_each_statement_independently(tmp_path, monkeypatch):
    statements = [
        STATEMENT,
        {"statement_id": "dream:second", "content_utf8": "The deployment color is green.", "source_handle": None, "context_refs": []},
    ]
    built = build_batch_placement_prompt(statements, str(tmp_path), "batch-partial")
    empty = [item for item in built["candidates"] if item["occupancy"]["count"] == 0]
    decisions = [
        {"statement_id": statement["statement_id"], "outcome": "apply", "action": "expand_surface", "candidate_id": empty[index]["candidate_id"], "reason_text": "independent durable fact"}
        for index, statement in enumerate(statements)
    ]
    original_apply = AccessRuntime.apply

    def fail_second(runtime, decision):
        if decision.statement_id == "dream:second":
            raise OSError("injected second admission failure")
        return original_apply(runtime, decision)

    monkeypatch.setattr(AccessRuntime, "apply", fail_second)
    applied = apply_batch_placement(
        json.dumps({"schema_version": BATCH_PLACEMENT_SCHEMA_VERSION, "decisions": decisions}),
        statements, str(tmp_path), "batch-partial", built["view_fingerprint"],
    )
    assert [item["outcome"] for item in applied["outcomes"]] == ["applied", "error"]
    with AccessMemoryLoop(tmp_path) as loop:
        assert loop.binding("dream:test")["current_statement_id"] == "dream:test"
        with pytest.raises(KeyError):
            loop.binding("dream:second")


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


def test_revision_confirmation_wire_rejects_without_write_and_blacklists_target(tmp_path):
    old = MemoryStatement("alpha:bx", "Alpha V3.9 release code is BX-3917.")
    new = {"statement_id": "caold:cr", "content_utf8": "CAOLD broad-residue acceptance code is CR-7159.", "source_handle": None, "context_refs": []}
    with AccessMemoryLoop(tmp_path) as loop:
        first = loop.apply_placement(old, json.loads(placement(old.statement_id, "expand_surface", "placement:expand:0")), "old")
    raw = json.dumps({
        "schema_version": PLACEMENT_SCHEMA_VERSION,
        "outcome": "apply",
        "decision": {
            "statement_id": new["statement_id"],
            "action": "revision_current",
            "candidate_id": "placement:existing:0",
            "existing_handle": first["handle"],
            "reason_text": "analogous field was incorrectly treated as revision",
        },
    })
    provisional_result = apply_placement(raw, new, str(tmp_path), "wrong", CELL)
    provisional = provisional_result["provisional_revision"]
    assert provisional_result["outcome"] == "revision_confirmation_required"
    assert provisional_result["core_write_count"] == 0
    built = build_revision_confirmation_prompt(provisional)
    assert "same subject or referent" in built["prompt"]
    reject_raw = json.dumps({
        "schema_version": "nollm_openclaw_revision_confirmation_v1",
        "outcome": "reject_revision",
        "relation": "different_subject_or_non_superseding",
    })
    parsed = parse_revision_confirmation(reject_raw, provisional)
    rejected = apply_placement(raw, new, str(tmp_path), "wrong", CELL, parsed["confirmation"])
    assert rejected["outcome"] == "revision_rejected"
    assert rejected["core_write_count"] == 0
    redecision = build_revision_redecision_prompt("original placement prompt", provisional, parsed["confirmation"])
    assert redecision["excluded_revision_targets"] == [first["handle"]]
    with pytest.raises(FormationAdapterError) as error:
        apply_placement(raw, new, str(tmp_path), "wrong", CELL, None, redecision["excluded_revision_targets"])
    assert error.value.category == "revision_target_excluded"
    with AccessMemoryLoop(tmp_path) as loop:
        assert loop.binding(old.statement_id)["current_statement_id"] == old.statement_id
