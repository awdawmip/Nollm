from pathlib import Path

from recall_lens.run_rev5_main_agent_scale_validation import run_validation


def test_rev5_main_agent_scale_validation_uses_declared_targets_and_measured_leakage(tmp_path: Path) -> None:
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
    assert summary["max_unrelated_leakage_count"] == 0
    assert summary["semantic_none_metric_available"] is False
    assert summary["geometry_function_gate_met"] is True
    assert summary["declared_target_simulation_gate_met"] is True
    assert summary["semantic_product_gate_met"] is False
    assert summary["provider_gate_met"] is False

    events = [__import__("json").loads(line) for line in (tmp_path / "evidence.jsonl").read_text(encoding="utf-8").splitlines()]
    queries = [event for event in events if event.get("event") == "query"]
    assert all(event["target_declared_before_recall"] is True for event in queries)
    assert all("returned_statement_ids" in event for event in queries)
