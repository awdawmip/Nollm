from __future__ import annotations

from nollm.grf.grf2_validation import baseline_comparison, failure_boundary_report, scale_metrics


def test_grf2_scale_metrics_cover_large_sizes_and_hard_conditions() -> None:
    for size in (10_000, 100_000, 1_000_000):
        metrics = scale_metrics(size, "uniform")
        assert metrics.dataset_size == size
        assert metrics.runtime_polygon_count == 0
        assert metrics.runtime_float_count_exact_profile == 0
        assert metrics.average_kernel_fanout <= 7
        assert metrics.relation_storage_size < metrics.explicit_graph_storage_size
        assert metrics.source_fallback_preserved is True


def test_grf2_failure_boundaries_and_baselines_are_reported() -> None:
    failures = failure_boundary_report()
    baselines = baseline_comparison(100_000)
    assert {item["failure"] for item in failures} == {"density_overload", "wrong_placement", "false_stitch", "profile_conflict"}
    assert {"B0_lexical", "B1_vector_like", "B2_explicit_graph", "B3_graph_vector", "N0_GRF_exact", "N1_GRF_stitching", "N2_GRF_multi_profile", "N3_GRF_incremental"} <= set(baselines)
    assert baselines["N3_GRF_incremental"]["storage"] < baselines["B2_explicit_graph"]["storage"]
