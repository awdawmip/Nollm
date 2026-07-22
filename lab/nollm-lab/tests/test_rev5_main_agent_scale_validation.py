from pathlib import Path

from recall_lens.run_rev5_main_agent_scale_validation import run_validation


def test_rev5_main_agent_scale_validation_meets_synthetic_thresholds(tmp_path: Path) -> None:
    summary = run_validation(
        tmp_path / "workspace",
        tmp_path / "evidence.jsonl",
        tmp_path / "summary.json",
    )
    assert summary["statement_count"] == 80
    assert summary["locality_count"] == 8
    assert summary["independent_unrelated_seed_count"] == 20
    assert summary["target_reach"] >= 0.9
    assert summary["expanded_target_reach"] == 1.0
    assert summary["default_result_p95"] <= 5
    assert summary["default_chars_p95"] <= 3000
    assert summary["single_entry_rate"] == 1.0
    assert summary["hidden_child_calls"] == 0
    assert summary["synthetic_thresholds_met"] is True
    assert summary["provider_gate_met"] is False
