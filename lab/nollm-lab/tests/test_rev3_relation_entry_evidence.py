from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
VALIDATION = ROOT / "validation"


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _rows(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _canonical(rows: list[dict[str, object]]) -> bytes:
    return b"".join(
        json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"
        for item in rows
    )


def test_rev3_frozen_evidence_preserves_passed_causal_gate_and_failed_growth_gate() -> None:
    evidence_path = VALIDATION / "aold_prompt_bounded_cartography_relation_recall_20260718.jsonl"
    summary = json.loads((VALIDATION / "aold_prompt_bounded_cartography_relation_recall_summary_20260718.json").read_text(encoding="utf-8"))
    evidence_bytes = evidence_path.read_bytes()
    rows = _rows(evidence_path)
    counts = Counter(item["record_type"] for item in rows)

    assert counts == {
        "provider_attempt": 32,
        "relation_entry_case": 10,
        "provider_free_field_growth": 1,
    }
    assert evidence_bytes == _canonical(rows)
    assert summary["evidence_line_count"] == len(rows) == 43
    assert summary["evidence_utf8_bytes"] == len(evidence_bytes)
    assert summary["evidence_sha256"] == _sha(evidence_bytes)
    assert summary["provider_causal_gate_passed"] is True
    assert summary["writer_durable_count"] == 10
    assert summary["relation_entry_reader_target_reach_count"] == 10
    assert summary["nonempty_target_path_count"] == 10
    assert summary["forced_lens_entry_reach_count"] == 10
    assert summary["unrelated_false_reach_count"] == 0
    assert summary["passed"] is False
    assert summary["completion_status"] == "AOLD_PROMPT_BOUNDED_CARTOGRAPHY_IN_PROGRESS"


def test_rev3_live_growth_record_binds_chat_and_host_bytes() -> None:
    evidence = _rows(VALIDATION / "aold_prompt_bounded_cartography_relation_recall_20260718.jsonl")
    growth = next(item for item in evidence if item["record_type"] == "provider_free_field_growth")
    live_path = VALIDATION / "aold_prompt_bounded_cartography_live_chat_20260718.jsonl"
    host_path = VALIDATION / "aold_prompt_bounded_cartography_live_host_20260718.jsonl"
    live_rows = _rows(live_path)

    assert growth["live_chat_count"] == 9
    assert growth["live_chat_process_success_count"] == 9
    assert growth["live_chat_sha256"] == _sha(_canonical(live_rows))
    assert growth["host_trace_sha256"] == _sha(host_path.read_bytes())
    assert growth["capture_state_counts"] == {"admitted": 1, "captured": 4, "processing": 4}
    assert growth["t0_statement_count"] == 2
    assert growth["t0_occupied_cell_count"] == 2
    assert growth["placement_count"] == 2
    assert growth["one_statement_atom_cell_achieved"] is False
    assert growth["long_arms_validated"] is False
    assert growth["gate_status"] == "IN_PROGRESS"
    assert growth["gateway_listener_present_at_freeze"] is False


def test_rev3_distribution_manifest_declares_active_bounded_wires() -> None:
    manifest = json.loads((ROOT / "distributions/nollm-openclaw/manifest.json").read_text(encoding="utf-8"))

    assert manifest["propositionWriterWire"] == "nollm_openclaw_proposition_writer_v1"
    assert manifest["fieldCartographerWire"] == "nollm_openclaw_field_cartographer_v1"
    assert manifest["progressiveAtlasPageWire"] == "nollm_access_progressive_atlas_page_v1"
    assert manifest["localDetailPageWire"] == "nollm_access_local_detail_page_v1"
    assert manifest["fastRecallWire"] == "nollm_openclaw_single_call_entry_recall_v1"
    assert manifest["cartographerMaxRegions"] == 32
    assert manifest["cartographerMaxPromptBytes"] == 65536
    assert manifest["cartographerMaxTurns"] == 4
    assert manifest["evidenceFilenameContract"] == "run_scoped_live_then_immutable_freeze_v1"
