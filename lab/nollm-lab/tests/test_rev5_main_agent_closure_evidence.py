from pathlib import Path

from evidence.verify_rev5_main_agent_closure_evidence import verify


ROOT = Path(__file__).resolve().parents[3]


def test_rev5_main_agent_closure_evidence_is_recomputable_and_not_live_claimed():
    computed = verify(
        ROOT / "validation/aold_main_agent_provider_live_selectivity_20260722.jsonl",
        ROOT / "validation/aold_main_agent_provider_live_selectivity_summary_20260722.json",
    )
    assert computed == {
        "target_reach": 1.0,
        "expanded_target_reach": 1.0,
        "cold_restart_reach": 1.0,
        "max_unrelated_leakage_count": 0,
    }
