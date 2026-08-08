from __future__ import annotations

from nollm_access import (
    AccessDecision,
    AccessRuntime,
    FileHandleStore,
    FileStatementStore,
    MemoryStatement,
    ProgressiveAtlasPolicy,
)
from nollm_access.memory_loop import DEFAULT_FIELD_SCOPE
from nollm_core import CoreRuntime, GeometryAddress
from nollm_openclaw_formation.field_encounter import (
    build_field_encounter_prompt,
    parse_field_encounter_decision,
    render_field_encounter_injection,
    run_field_encounter,
)


def _seed(workspace) -> None:
    core = CoreRuntime(workspace)
    access = AccessRuntime(core, FileStatementStore(workspace), FileHandleStore(workspace))
    statement = MemoryStatement("existing", "The meeting place is room 401.", context_refs=("capture:seed",))
    access.capture(statement)
    access.apply(
        AccessDecision(
            "seed:existing",
            statement.statement_id,
            "new",
            target_cell=GeometryAddress("default_dream_v1", "default", 0, 0, 0),
            reason_text="fixture seed",
            decided_by="fixture",
        )
    )
    access.close()
    core.close()


def _request(pending=None):
    return {
        "scope_id": "scope:test",
        "workspace_id": "workspace:test",
        "stimulus_material": ["Where was the meeting?"],
        "optional_pending_proposition": pending,
        "field_scope": DEFAULT_FIELD_SCOPE.to_mapping(),
        "surface_policy": ProgressiveAtlasPolicy().to_mapping(),
        "locality_max_results": 8,
        "locality_max_chars": 6000,
        "vacancy_budget": 8,
        "expected_state_identity": None,
        "created_at_ms": None,
        "ttl_ms": 60000,
    }


def _enter_history(surface):
    region = next(item for item in surface["page"]["regions"] if item["support_entries"])
    entry = region["support_entries"][0]
    return [{"action": "enter_locality", "region_id": region["region_id"], "entry_id": entry["entry_id"]}]


def test_bridge_replays_query_operation_without_exposing_physical_addresses(tmp_path):
    _seed(tmp_path)
    workspace = str(tmp_path)
    surface = run_field_encounter(workspace, "query", _request(), [])
    history = _enter_history(surface)
    locality = run_field_encounter(workspace, "query", surface["request"], history)
    fact = next(item for item in locality["facts"] if item["statement_id"] == "existing")
    result = run_field_encounter(
        workspace,
        "query",
        surface["request"],
        history,
        {"action": "select_fact", "candidate_id": fact["fact_id"], "semantic_relation": "same", "recalled_fact_ids": []},
    )
    assert result["effect"]["effect_kind"] == "recall"
    assert result["recalled_statement_ids"] == ["existing"]
    assert "entry_cell" not in locality
    assert all("address" not in item for item in locality["vacancies"])


def test_bridge_replays_pending_terminal_and_conditionally_commits(tmp_path):
    _seed(tmp_path)
    pending = {
        "proposition_id": "new-statement",
        "content_utf8": "The next meeting is on Wednesday.",
        "evidence_refs": ["capture:new"],
        "origin_kinds": ["user"],
        "derived_from_statement_ids": [],
        "formation_version": "fixture-writer-v1",
    }
    workspace = str(tmp_path)
    surface = run_field_encounter(workspace, "write", _request(pending), [])
    history = _enter_history(surface)
    locality = run_field_encounter(workspace, "write", surface["request"], history)
    vacancy = next(item for item in locality["vacancies"] if item["vacancy_kind"] != "NEUTRAL_SEED_VACANCY")
    terminal = {
        "action": "select_vacancy",
        "candidate_id": vacancy["vacancy_id"],
        "semantic_relation": "related_distinct",
        "recalled_fact_ids": [],
    }
    committed = run_field_encounter(
        workspace,
        "write",
        surface["request"],
        history,
        terminal,
        {
            "statement": MemoryStatement(
                pending["proposition_id"],
                pending["content_utf8"],
                context_refs=tuple(pending["evidence_refs"]),
            ).to_mapping(),
            "revision_confirmation": None,
        },
    )
    assert committed["effect"]["effect_kind"] == "place"
    assert committed["commit"]["commit_state"] == "committed_and_verified"
    assert committed["commit"]["core_write_count"] == 1


def test_writer_prompt_and_parser_accept_only_visible_encounter_ids(tmp_path):
    _seed(tmp_path)
    pending = {
        "proposition_id": "pending",
        "content_utf8": "A related fact.",
        "evidence_refs": ["capture:new"],
        "origin_kinds": ["user"],
        "derived_from_statement_ids": [],
        "formation_version": "fixture-writer-v1",
    }
    surface = run_field_encounter(str(tmp_path), "prompt", _request(pending), [])
    built = build_field_encounter_prompt(surface, pending, 1)
    assert built["status"] == "encounter_decision"
    region = surface["page"]["regions"][0]
    entry = region["support_entries"][0]
    decision = parse_field_encounter_decision(
        '{"action":"enter_locality","region_id":"%s","entry_id":"%s"}'
        % (region["region_id"], entry["entry_id"]),
        surface,
    )
    assert decision["entry_id"] == entry["entry_id"]


def test_direct_encounter_activation_rereads_current_statement_and_skips_stale_ids(tmp_path):
    _seed(tmp_path)
    rendered = render_field_encounter_injection(
        ["missing", "existing"],
        str(tmp_path),
        max_statements=8,
        max_chars=6000,
    )
    assert rendered["outcome"] == "inject"
    assert rendered["statement_ids"] == ["existing"]
    assert rendered["stale_statement_ids"] == ["missing"]
    assert rendered["current_statement_projection"] is True
    assert rendered["operation_local"] is True
    assert rendered["persistent_state_written"] is False
    assert "room 401" in rendered["injection"]


def test_direct_encounter_activation_is_bounded_and_marks_truncation(tmp_path):
    _seed(tmp_path)
    rendered = render_field_encounter_injection(
        ["existing"],
        str(tmp_path),
        max_statements=1,
        max_chars=12,
    )
    assert rendered["outcome"] == "inject"
    assert rendered["truncated"] is True
    assert rendered["rendered_chars"] == 12
    assert rendered["statement_ids"] == ["existing"]
    assert "[Additional geometry memory omitted" in rendered["injection"]


def test_direct_encounter_activation_all_stale_is_none_and_writes_nothing(tmp_path):
    rendered = render_field_encounter_injection(
        ["missing"], str(tmp_path), max_statements=8, max_chars=6000
    )
    assert rendered["outcome"] == "none"
    assert rendered["injection"] == ""
    assert rendered["statement_ids"] == []
    assert rendered["stale_statement_ids"] == ["missing"]
    assert not (tmp_path / "direct_activation").exists()
