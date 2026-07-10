from __future__ import annotations

from integrations.adapters.grf7r2_long_running import run_sustained_mutation


def test_sustained_mutation_ledger_counts_real_operations(tmp_path) -> None:
    result = run_sustained_mutation(tmp_path, operation_count=1_000, checkpoint_interval=100, mutation_count=10)

    assert result["operation_count"] == 1_000
    assert result["operation_counts"]["capture"] == 10
    assert result["operation_counts"]["place"] == 10
    assert result["operation_counts"]["admit"] == 10
    assert result["real_post_commit_retry_count"] == 10
    assert result["recovery_count"] == result["injected_failure_count"]
    assert result["duplicate_evidence_count"] == result["duplicate_placement_count"] == result["duplicate_admission_count"] == 0
    assert result["snapshot_replay_equals_final_state"] is True
