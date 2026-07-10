from nollm.grf.grf8_quality_dataset import CATEGORIES, QUERY_TYPES, build_quality_dataset, dataset_digest
from nollm.grf.grf8_quality_benchmark import benchmark, compare_baselines


def test_quality_dataset_has_six_categories_and_deterministic_truth() -> None:
    first = build_quality_dataset(60, 60)
    second = build_quality_dataset(60, 60)
    assert {item.category for item in first[0]} == set(CATEGORIES)
    assert {item.query_type for item in first[1]} == set(QUERY_TYPES)
    assert all(item.relevant_shard_ids and item.hard_negative_shard_ids for item in first[1])
    assert dataset_digest(*first) == dataset_digest(*second)
    metrics = benchmark(*first)
    assert metrics.source_faithfulness == 1.0
    assert 0.0 <= metrics.false_relation_rate <= 1.0
    models = compare_baselines(*first)
    assert set(models) == {"B0_lexical", "B1_bm25_like", "B2_vector_like", "B3_explicit_graph", "B4_graph_vector_like", "N0_evidence_only", "N1_local_geometry", "N2_coverage_propagation", "N3_global_sharded_grf", "N4_grf_stitching", "N5_grf_revision_awareness"}
    assert models["B2_vector_like"] != models["N5_grf_revision_awareness"]
    assert models["N4_grf_stitching"].missed_stitch_rate < models["N3_global_sharded_grf"].missed_stitch_rate
    assert models["N5_grf_revision_awareness"].revision_correctness > models["N4_grf_stitching"].revision_correctness
    assert models["N5_grf_revision_awareness"].storage_bytes > 0
    assert models["N5_grf_revision_awareness"].query_latency_ms >= 0.0
