from __future__ import annotations

from nollm.grf.production_reality_benchmark import run_reality_benchmark


def test_reality_benchmark_executes_full_core_pipeline_with_measured_metrics() -> None:
    metrics = run_reality_benchmark(100)
    assert metrics.dataset_size == 100
    assert metrics.items_per_second > 0 and metrics.bytes_per_second > 0
    assert metrics.evidence_storage_size > 0
    assert metrics.placement_storage_size > 0
    assert metrics.admission_storage_size > 0
    assert metrics.relation_storage_size > 0
    assert metrics.source_fallback_success == "100/100"
    assert metrics.recall_correctness == "1/1"
    assert metrics.source_faithfulness == "1/1"


def test_kernel_and_template_serialized_storage_is_stable_across_dataset_sizes() -> None:
    small = run_reality_benchmark(10)
    larger = run_reality_benchmark(20)
    assert small.kernel_storage_size == larger.kernel_storage_size
    assert small.template_storage_size == larger.template_storage_size
