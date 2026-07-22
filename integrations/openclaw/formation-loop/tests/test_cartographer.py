import json

import pytest

from nollm_access import AccessMemoryLoop, FileStatementProvenanceStore, FileStatementStore

from nollm_openclaw_formation.cartographer import (
    FIELD_CARTOGRAPHER_SCHEMA_VERSION,
    LEGACY_PROPOSITION_WRITER_SCHEMA_VERSION,
    PROPOSITION_WRITER_SCHEMA_VERSION,
    advance_field_cartographer,
    apply_field_cartography_result,
    build_field_cartographer_prompt,
    build_proposition_writer_prompt,
    migrate_legacy_proposition_writer_result,
    parse_proposition_writer_result,
)
from nollm_openclaw_formation.memory_loop import (
    BATCH_PLACEMENT_SCHEMA_VERSION,
    apply_batch_placement,
    build_batch_placement_prompt,
)


CAPTURE = {
    "capture_id": "capture-one",
    "user_utf8": "今天东京下雨了。",
    "assistant_utf8": "收到。",
    "captured_epoch_ms": 1_784_361_600_000,
    "timezone_offset_minutes": 480,
}


def _writer_raw(content="2026年7月18日东京下雨。"):
    return json.dumps({
        "schema_version": PROPOSITION_WRITER_SCHEMA_VERSION,
        "outcome": "plan",
        "propositions": [{
            "draft_id": "d1",
            "outcome": "statement",
            "content_utf8": content,
            "source_capture_ids": ["capture-one"],
            "context_capture_ids": [],
            "evidence_refs": [{
                "evidence_ref_id": "e1", "capture_id": "capture-one", "role": "user", "quote_utf8": CAPTURE["user_utf8"],
            }],
            "resolved_references": [{
                "reference_id": "r1",
                "kind": "temporal", "normalized_value": "2026-07-18",
                "basis_evidence_ref_ids": [], "timestamp_basis_capture_ids": ["capture-one"],
            }],
            "direct_queries": [{"query_id": "direct-tokyo", "query_utf8": "东京天气如何？"}],
            "entry_queries": [{"query_id": "entry-tokyo", "query_utf8": "这次东京经历发生了什么？"}],
        }],
        "defer_reason": None,
    }, ensure_ascii=False)


def _writer_result(request_id="writer"):
    return parse_proposition_writer_result(_writer_raw(), [CAPTURE], request_id)


def _seed_field(workspace, count):
    outcomes = []
    offset = 0
    while offset < count:
        statements = [
            {"statement_id": f"seed:{index}", "content_utf8": str(index), "source_handle": None, "context_refs": []}
            for index in range(offset, min(offset + 16, count))
        ]
        request_id = f"seed-batch:{offset}"
        built = build_batch_placement_prompt(statements, str(workspace), request_id, 1, 16)
        empty = [item for item in built["candidates"] if item["occupancy"]["count"] == 0]
        assert empty
        statements = statements[:len(empty)]
        decisions = [
            {"statement_id": statement["statement_id"], "outcome": "apply", "action": "expand_surface" if empty[index]["relation_kind"] == "expand_surface" else "new_local", "candidate_id": empty[index]["candidate_id"], "reason_text": "bounded test field"}
            for index, statement in enumerate(statements)
        ]
        applied = apply_batch_placement(
            json.dumps({"schema_version": BATCH_PLACEMENT_SCHEMA_VERSION, "decisions": decisions}),
            statements, str(workspace), request_id, built["view_fingerprint"], 1, 16,
        )
        assert all(item["outcome"] == "applied" for item in applied["outcomes"])
        outcomes.extend(applied["outcomes"])
        offset += len(statements)
    return outcomes


def test_writer_is_context_bounded_and_field_size_independent(tmp_path):
    empty = build_proposition_writer_prompt([CAPTURE], "writer", context_captures=[])
    assert empty["context_captures"] == []
    assert empty["context_capture_count"] == 0
    _seed_field(tmp_path, 1)
    populated = build_proposition_writer_prompt([CAPTURE], "writer", context_captures=[])

    assert empty["prompt"] == populated["prompt"]
    assert empty["field_input_count"] == 0
    assert empty["prompt_utf8_bytes"] < 65536
    assert "progressive_atlas_page:" not in empty["prompt"]
    assert "locality_atlas:" not in empty["prompt"]
    assert "candidate_id" not in empty["prompt"]
    assert "Never calculate or output start, end" in empty["prompt"]
    assert "span-array indexes" in empty["prompt"]
    assert "Evidence quote refs" in empty["prompt"]
    assert "Prefer user-role quotes" in empty["prompt"]
    assert 'outcome must be the literal string "plan"' in empty["prompt"]
    assert "Every proposition object must contain exactly these nine keys" in empty["prompt"]
    assert "basis_evidence_ref_ids cross-link" in empty["prompt"]
    assert "source_capture_ids may contain only IDs listed in absorption_sources" in empty["prompt"]
    assert 'Proposition outcome must be "statement"' in empty["prompt"]


def test_context_writer_resolves_same_day_with_explicit_prior_capture_provenance():
    context = {
        "capture_id": "capture-context", "user_utf8": "2026年7月21日我参加了线上会议。", "assistant_utf8": "收到。",
        "captured_epoch_ms": 1_784_563_200_000, "timezone_offset_minutes": 480,
    }
    source = {
        "capture_id": "capture-source", "user_utf8": "那天晚上我整理了会议记录。", "assistant_utf8": "好的。",
        "captured_epoch_ms": 1_784_606_400_000, "timezone_offset_minutes": 480,
    }
    raw = json.dumps({
        "schema_version": PROPOSITION_WRITER_SCHEMA_VERSION, "outcome": "plan", "defer_reason": None,
        "propositions": [{
            "draft_id": "d1", "outcome": "statement", "content_utf8": "2026年7月21日晚上，用户整理了该线上会议的记录。",
            "source_capture_ids": [source["capture_id"]], "context_capture_ids": [context["capture_id"]],
            "evidence_refs": [
                {"evidence_ref_id": "context-date", "capture_id": context["capture_id"], "role": "user", "quote_utf8": context["user_utf8"]},
                {"evidence_ref_id": "source-event", "capture_id": source["capture_id"], "role": "user", "quote_utf8": source["user_utf8"]},
            ],
            "resolved_references": [{
                "reference_id": "same-day",
                "kind": "temporal", "normalized_value": "2026-07-21",
                "basis_evidence_ref_ids": ["context-date"], "timestamp_basis_capture_ids": [],
            }],
            "direct_queries": [{"query_id": "direct-1", "query_utf8": "用户那天晚上做了什么？"}],
            "entry_queries": [{"query_id": "entry-1", "query_utf8": "这次线上会议发生了什么？"}],
        }],
    }, ensure_ascii=False)

    built = build_proposition_writer_prompt([source], "contextual", context_captures=[context])
    parsed = parse_proposition_writer_result(raw, [source], "contextual", context_captures=[context])
    assert built["context_capture_count"] == 1
    assert built["context_chars"] <= 6000
    assert "context_only_evidence" in built["prompt"]
    assert parsed["context_capture_ids"] == [context["capture_id"]]
    assert parsed["propositions"][0]["direct_queries"][0]["query_utf8"] != parsed["propositions"][0]["entry_queries"][0]["query_utf8"]

    wrong = json.loads(raw)
    wrong["propositions"][0]["content_utf8"] = "2026年7月20日晚上，用户整理了该线上会议的记录。"
    wrong["propositions"][0]["resolved_references"][0]["normalized_value"] = "2026-07-20"
    with pytest.raises(Exception, match="no Evidence basis"):
        parse_proposition_writer_result(json.dumps(wrong, ensure_ascii=False), [source], "wrong-date", context_captures=[context])


def test_context_only_capture_cannot_become_absorption_source():
    context = {**CAPTURE, "capture_id": "context", "captured_epoch_ms": CAPTURE["captured_epoch_ms"] - 1}
    raw = json.loads(_writer_raw())
    raw["propositions"][0]["source_capture_ids"] = ["context"]
    with pytest.raises(Exception, match="source Capture IDs"):
        parse_proposition_writer_result(json.dumps(raw, ensure_ascii=False), [CAPTURE], "context-source", context_captures=[context])


def test_memory_derived_assistant_cannot_be_new_statement_source():
    capture = {
        **CAPTURE,
        "user_role_mode": "source",
        "assistant_role_mode": "memory_derived",
        "memory_tool_actions": ["recall", "surface"],
        "recalled_statement_ids": ["old-statement"],
    }
    raw = json.loads(_writer_raw("收到。"))
    proposition = raw["propositions"][0]
    proposition["evidence_refs"] = [{
        "evidence_ref_id": "assistant-echo", "capture_id": CAPTURE["capture_id"],
        "role": "assistant", "quote_utf8": CAPTURE["assistant_utf8"],
    }]
    proposition["resolved_references"] = []
    with pytest.raises(Exception, match="assistant role is not eligible"):
        parse_proposition_writer_result(json.dumps(raw, ensure_ascii=False), [capture], "memory-echo")

    built = build_proposition_writer_prompt([capture], "memory-echo-prompt")
    assert "memory_derived may help understand the turn" in built["prompt"]


def test_active_writer_rejects_legacy_and_explicit_migration_marks_coarse_provenance():
    raw = json.dumps({
        "schema_version": LEGACY_PROPOSITION_WRITER_SCHEMA_VERSION, "outcome": "plan", "defer_reason": None,
        "propositions": [{
            "draft_id": "d1", "content_utf8": "东京下雨。", "source_capture_ids": [CAPTURE["capture_id"]],
            "lenses": [{
                "lens_id": "legacy-lens", "future_query": "东京天气如何？",
                "basis_spans": [{"capture_id": CAPTURE["capture_id"], "role": "user", "start": 0, "end": len(CAPTURE["user_utf8"]), "quote_utf8": CAPTURE["user_utf8"]}],
            }],
        }],
    }, ensure_ascii=False)
    with pytest.raises(Exception, match="invalid Proposition Writer envelope"):
        parse_proposition_writer_result(raw, [CAPTURE], "legacy-active")
    migrated = migrate_legacy_proposition_writer_result(raw, [CAPTURE], "legacy-migration")
    proposition = migrated["propositions"][0]
    assert migrated["provenance_precision"] == "coarse"
    assert proposition["direct_queries"] == [{"query_id": "legacy-lens", "query_utf8": "东京天气如何？"}]
    assert proposition["entry_queries"] == proposition["direct_queries"]


def test_cartographer_independent_seed_then_related_growth(tmp_path):
    writer = _writer_result("seed-writer")
    built = build_field_cartographer_prompt(writer, str(tmp_path), "seed")
    assert "existing region need not already contain the new answer" in built["prompt"]
    assert "keyword overlap alone" in built["prompt"]
    assert "no two resolved entry queries may select support entries with the same entry_cell" in built["prompt"]
    entry_query = writer["propositions"][0]["entry_queries"][0]
    independent_raw = json.dumps({
        "schema_version": FIELD_CARTOGRAPHER_SCHEMA_VERSION,
        "action": "resolve",
        "plans": [{
            "draft_id": "d1", "placement_mode": "independent_seed",
            "entry_resolutions": [{"entry_query_id": entry_query["query_id"], "region_id": None, "entry_id": None, "unresolved": True}],
            "existing_handle": None, "reason_text": "no credible relation",
        }],
    })
    resolved = advance_field_cartographer(independent_raw, writer, built["page"], str(tmp_path), "seed", 1)
    applied = apply_field_cartography_result(resolved, writer, [CAPTURE], str(tmp_path), "seed")
    seed = applied["outcomes"][0]
    assert seed["outcome"] == "applied" and seed["placement_mode"] == "independent_seed"
    with AccessMemoryLoop(tmp_path) as loop:
        provenance = loop.statement_provenance(seed["statement_id"])
    assert provenance["writer_schema_version"] == PROPOSITION_WRITER_SCHEMA_VERSION
    assert provenance["source_capture_ids"] == [CAPTURE["capture_id"]]
    assert provenance["evidence_spans"][0]["quote_utf8"] == CAPTURE["user_utf8"]
    assert seed["provenance_sha256"] == provenance["provenance_sha256"]

    second_writer = parse_proposition_writer_result(_writer_raw("用户因东京降雨取消浅草行程。"), [CAPTURE], "related-writer")
    related_built = build_field_cartographer_prompt(second_writer, str(tmp_path), "related")
    region = related_built["page"]["regions"][0]
    entry = region["support_entries"][0]
    related_raw = json.dumps({
        "schema_version": FIELD_CARTOGRAPHER_SCHEMA_VERSION,
        "action": "resolve",
        "plans": [{
            "draft_id": "d1", "placement_mode": "related_growth",
            "entry_resolutions": [{
                "entry_query_id": second_writer["propositions"][0]["entry_queries"][0]["query_id"],
                "region_id": region["region_id"], "entry_id": entry["entry_id"], "unresolved": False,
            }],
            "existing_handle": None, "reason_text": "Tokyo relation",
        }],
    })
    related = advance_field_cartographer(related_raw, second_writer, related_built["page"], str(tmp_path), "related", 1)
    related_applied = apply_field_cartography_result(related, second_writer, [CAPTURE], str(tmp_path), "related")
    assert related_applied["outcomes"][0]["outcome"] == "applied"
    assert related_applied["outcomes"][0]["placement_mode"] == "related_growth"


def _independent_cartography(writer, workspace, request_id):
    built = build_field_cartographer_prompt(writer, str(workspace), request_id)
    query = writer["propositions"][0]["entry_queries"][0]
    raw = json.dumps({
        "schema_version": FIELD_CARTOGRAPHER_SCHEMA_VERSION,
        "action": "resolve",
        "plans": [{
            "draft_id": "d1", "placement_mode": "independent_seed",
            "entry_resolutions": [{"entry_query_id": query["query_id"], "region_id": None, "entry_id": None, "unresolved": True}],
            "existing_handle": None, "reason_text": "independent fixture",
        }],
    })
    return advance_field_cartographer(raw, writer, built["page"], str(workspace), request_id, 1)


def test_cartography_plan_rejects_field_change_before_any_apply_write(tmp_path):
    writer = _writer_result("stale-writer")
    resolved = _independent_cartography(writer, tmp_path, "stale")
    _seed_field(tmp_path, 1)
    with AccessMemoryLoop(tmp_path) as loop:
        before = loop.core_state_sha256()
        occupied_before = loop.build_progressive_atlas("stale:before").occupied_field_cell_count
    with pytest.raises(Exception, match="field state changed"):
        apply_field_cartography_result(resolved, writer, [CAPTURE], str(tmp_path), "stale")
    with AccessMemoryLoop(tmp_path) as loop:
        assert loop.core_state_sha256() == before
        assert loop.build_progressive_atlas("stale:after").occupied_field_cell_count == occupied_before
    assert not (tmp_path / "access" / "statement-provenance").exists()


def test_cartography_plan_token_tamper_is_zero_write(tmp_path):
    writer = _writer_result("token-writer")
    resolved = _independent_cartography(writer, tmp_path, "token")
    resolved["plan_token"]["page_fingerprint"] = "0" * 64
    with pytest.raises(Exception, match="not canonical"):
        apply_field_cartography_result(resolved, writer, [CAPTURE], str(tmp_path), "token")
    with AccessMemoryLoop(tmp_path) as loop:
        assert loop.build_progressive_atlas("token:after").occupied_field_cell_count == 0


def test_provenance_write_failure_rolls_back_new_statement_and_core(tmp_path, monkeypatch):
    writer = _writer_result("provenance-failure-writer")
    resolved = _independent_cartography(writer, tmp_path, "provenance-failure")

    def fail_put(_store, _value):
        raise OSError("injected provenance failure")

    monkeypatch.setattr(FileStatementProvenanceStore, "put", fail_put)
    applied = apply_field_cartography_result(resolved, writer, [CAPTURE], str(tmp_path), "provenance-failure")
    outcome = applied["outcomes"][0]
    assert outcome["outcome"] == "error"
    assert "injected provenance failure" in outcome["error"]
    assert not FileStatementStore(tmp_path).exists(outcome["statement_id"])
    assert not FileStatementProvenanceStore(tmp_path).exists(outcome["statement_id"])
    with AccessMemoryLoop(tmp_path) as loop:
        assert loop.build_progressive_atlas("provenance-failure:after").occupied_field_cell_count == 0


def test_cartographer_uses_one_session_across_progressive_turns(tmp_path):
    _seed_field(tmp_path, 40)
    writer = _writer_result()
    first = build_field_cartographer_prompt(writer, str(tmp_path), "cartography")
    region = first["page"]["regions"][-1]
    opened = advance_field_cartographer(json.dumps({
        "schema_version": FIELD_CARTOGRAPHER_SCHEMA_VERSION,
        "action": "open_region",
        "region_id": region["region_id"],
    }), writer, first["page"], str(tmp_path), "cartography", 1)

    assert first["turn"] == 1 and opened["turn"] == 2
    assert first["max_turns"] == opened["max_turns"] == 4
    assert first["atlas_fingerprint"] == opened["atlas_fingerprint"]
    assert opened["prompt_utf8_bytes"] <= 65536
    assert opened["page"]["coverage_certificate"]["uncovered_source_cell_count"] == 0


def test_cartographer_requests_bounded_local_detail_in_same_operation(tmp_path):
    _seed_field(tmp_path, 1)
    writer = _writer_result("detail-writer")
    first = build_field_cartographer_prompt(writer, str(tmp_path), "detail")
    region_id = first["page"]["regions"][0]["region_id"]
    detailed = advance_field_cartographer(json.dumps({
        "schema_version": FIELD_CARTOGRAPHER_SCHEMA_VERSION,
        "action": "request_local_detail",
        "region_id": region_id,
    }), writer, first["page"], str(tmp_path), "detail", 1)

    assert detailed["status"] == "cartographer_decision"
    assert detailed["turn"] == 2
    assert detailed["local_detail"]["region_id"] == region_id
    assert detailed["local_detail"]["has_more"] is False
    assert "local_detail_page:" in detailed["prompt"]
