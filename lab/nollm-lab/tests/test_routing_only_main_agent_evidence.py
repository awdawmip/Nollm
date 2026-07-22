from pathlib import Path

from evidence.verify_routing_only_main_agent_evidence import verify


ROOT = Path(__file__).resolve().parents[3]


def test_routing_only_evidence_is_recomputable_and_never_claims_live_semantics():
    computed = verify(
        ROOT / "validation/aold_routing_only_real_main_agent_live_20260722.jsonl",
        ROOT / "validation/aold_routing_only_real_main_agent_live_summary_20260722.json",
    )
    assert computed["target_reach"] == 1.0
    assert computed["expanded_target_reach"] == 1.0
    assert computed["cold_restart_reach"] == 1.0
    assert computed["max_unrelated_leakage_count"] == 0
    assert computed["full_statement_leakage_count"] == 0
    assert computed["visible_json_utf8_bytes"] <= 8192
