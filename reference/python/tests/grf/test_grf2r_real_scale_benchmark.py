from __future__ import annotations

from nollm.grf.real_scale_benchmark import inject_failure_boundaries, run_incremental_equivalence, run_real_scale_benchmark


def test_real_scale_benchmark_routes_actual_records_through_field_engine() -> None:
    metrics = run_real_scale_benchmark(100)
    assert metrics.counts.shard_count == 100
    assert metrics.counts.placement_count == 100
    assert metrics.counts.island_count == 100
    assert metrics.field_engine_executed is True
    assert metrics.relation_field_executed is True
    assert metrics.explicit_graph_materialized is True
    assert metrics.source_fallback_preserved is True
    assert metrics.explicit_graph_edge_count > 0


def test_incremental_result_matches_independent_full_rebuild() -> None:
    assert run_incremental_equivalence().all_equal is True


def test_failure_boundaries_are_executed_not_descriptive() -> None:
    failures = inject_failure_boundaries()
    assert failures["density_overload"]["migration_candidate"] is True
    assert failures["wrong_placement"]["revision_applied"] is True
    assert failures["false_stitch"]["rejected"] is True
    assert failures["false_stitch"]["rollback"] is True
