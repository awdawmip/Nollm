from __future__ import annotations

from nollm.grf.grf7r_workflow import run_workflow_benchmark


def test_workflow_metrics_are_computed_from_shared_ground_truth(tmp_path) -> None:
    result = run_workflow_benchmark(tmp_path, topics_per_workflow=2)

    assert result["workflow_count"] == 4
    assert result["roles"] == ("hard_negative", "relevant_primary", "relevant_secondary", "same_name_false_friend", "source_conflict", "temporal_conflict")
    assert result["false_relation_injected"] is True
    assert result["grf_false_bridge_used_before_rollback"] is True
    assert result["grf_false_bridge_used_after_rollback"] is False
    assert result["grf_rollback_success"] is True
    assert set(result["models"]) == {"B0_lexical", "B1_vector_like", "B2_explicit_graph", "B3_graph_vector", "N0_GRF"}
