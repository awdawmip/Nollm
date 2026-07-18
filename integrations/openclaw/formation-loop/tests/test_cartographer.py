import json

from nollm_core import CoreRuntime, GeometryAddress, MemoryAtom
from nollm_openclaw_formation.cartographer import (
    FIELD_CARTOGRAPHER_SCHEMA_VERSION,
    PROPOSITION_WRITER_SCHEMA_VERSION,
    advance_field_cartographer,
    apply_field_cartography_result,
    build_field_cartographer_prompt,
    build_proposition_writer_prompt,
    parse_proposition_writer_result,
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
            "content_utf8": content,
            "source_capture_ids": ["capture-one"],
            "lenses": [{
                "lens_id": "lens-tokyo",
                "future_query": "东京天气如何？",
                "basis_spans": [{
                    "capture_id": "capture-one", "role": "user", "start": 0,
                    "end": len(CAPTURE["user_utf8"]), "quote_utf8": CAPTURE["user_utf8"],
                }],
            }],
        }],
        "defer_reason": None,
    }, ensure_ascii=False)


def _writer_result(request_id="writer"):
    return parse_proposition_writer_result(_writer_raw(), [CAPTURE], request_id)


def test_writer_is_capture_only_and_field_size_independent(tmp_path):
    empty = build_proposition_writer_prompt([CAPTURE], "writer")
    with CoreRuntime(tmp_path) as core:
        for q in range(40):
            core.put(MemoryAtom(f"a{q}", str(q)), GeometryAddress("default_dream_v1", "default", 0, q, 0))
    populated = build_proposition_writer_prompt([CAPTURE], "writer")

    assert empty["prompt"] == populated["prompt"]
    assert empty["field_input_count"] == 0
    assert empty["prompt_utf8_bytes"] < 65536
    assert "progressive_atlas_page:" not in empty["prompt"]
    assert "locality_atlas:" not in empty["prompt"]
    assert "candidate_id" not in empty["prompt"]


def test_cartographer_independent_seed_then_related_growth(tmp_path):
    writer = _writer_result("seed-writer")
    built = build_field_cartographer_prompt(writer, str(tmp_path), "seed")
    lens = writer["propositions"][0]["lenses"][0]
    independent_raw = json.dumps({
        "schema_version": FIELD_CARTOGRAPHER_SCHEMA_VERSION,
        "action": "resolve",
        "plans": [{
            "draft_id": "d1", "placement_mode": "independent_seed",
            "lens_resolutions": [{"lens_id": lens["lens_id"], "region_id": None, "entry_id": None, "unresolved": True}],
            "existing_handle": None, "reason_text": "no credible relation",
        }],
    })
    resolved = advance_field_cartographer(independent_raw, writer, built["page"], str(tmp_path), "seed", 1)
    applied = apply_field_cartography_result(resolved, writer, [CAPTURE], str(tmp_path), "seed")
    seed = applied["outcomes"][0]
    assert seed["outcome"] == "applied" and seed["placement_mode"] == "independent_seed"

    second_writer = parse_proposition_writer_result(_writer_raw("用户因东京降雨取消浅草行程。"), [CAPTURE], "related-writer")
    related_built = build_field_cartographer_prompt(second_writer, str(tmp_path), "related")
    region = related_built["page"]["regions"][0]
    entry = region["support_entries"][0]
    related_raw = json.dumps({
        "schema_version": FIELD_CARTOGRAPHER_SCHEMA_VERSION,
        "action": "resolve",
        "plans": [{
            "draft_id": "d1", "placement_mode": "related_growth",
            "lens_resolutions": [{
                "lens_id": second_writer["propositions"][0]["lenses"][0]["lens_id"],
                "region_id": region["region_id"], "entry_id": entry["entry_id"], "unresolved": False,
            }],
            "existing_handle": None, "reason_text": "Tokyo relation",
        }],
    })
    related = advance_field_cartographer(related_raw, second_writer, related_built["page"], str(tmp_path), "related", 1)
    related_applied = apply_field_cartography_result(related, second_writer, [CAPTURE], str(tmp_path), "related")
    assert related_applied["outcomes"][0]["outcome"] == "applied"
    assert related_applied["outcomes"][0]["placement_mode"] == "related_growth"


def test_cartographer_uses_one_session_across_progressive_turns(tmp_path):
    with CoreRuntime(tmp_path) as core:
        for q in range(40):
            core.put(MemoryAtom(f"a{q}", str(q)), GeometryAddress("default_dream_v1", "default", 0, q, 0))
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
    with CoreRuntime(tmp_path) as core:
        core.put(MemoryAtom("a0", "zero"), GeometryAddress("default_dream_v1", "default", 0, 0, 0))
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
