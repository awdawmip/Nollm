from __future__ import annotations

from nollm.grf.grf7_cross_validation import run_grf7_cross_validation


def test_cross_validation_executes_bounded_queries_and_stitch_lifecycle() -> None:
    result = run_grf7_cross_validation(((1_000, 100), (10_000_000, 5_000)))
    final = result.workloads[-1]
    assert final.query_count == 5_000
    assert final.cross_partition_query_count == 5_000
    assert final.stitch_query_count == 1_000
    assert final.rollback_rejection_query_count == 1_000
    assert final.exact_identity_correct == 5_000
    assert final.source_fallback_correct == 5_000
    assert final.path_correct == 5_000
    assert final.max_loaded_partitions == 2
    assert result.reject_count == 2 and result.rollback_count == 1
    assert result.no_global_partition_scan is True
    assert result.replay_deterministic is True
    assert result.status == "GATE_B_PASS|GATE_C_PASS"
