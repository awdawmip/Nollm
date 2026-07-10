from __future__ import annotations

from nollm.grf.unified_scale_validation import run_unified_scale_validation


def test_unified_scale_validation_runs_real_bounded_pipeline() -> None:
    result = run_unified_scale_validation((100, 250), partition_size=100)
    assert result.generated_objects == 250
    assert result.field_build_count == 3
    assert result.recall_count == 3
    assert result.kernel_storage_independent is True
    assert result.source_fallback_preserved is True
    assert result.relation_growth_not_quadratic is True
    assert result.milestones[-1].source_fallback_success == "250/250"
    assert all(item.capture_latency_ns > 0 for item in result.milestones)
    assert all(item.placement_latency_ns > 0 for item in result.milestones)
    assert all(item.admission_latency_ns > 0 for item in result.milestones)
    assert all(item.rebuild_latency_ns > 0 for item in result.milestones)
    assert all(item.recall_latency_ns > 0 for item in result.milestones)
    assert all(item.update_latency_ns > 0 for item in result.milestones)


def test_unified_scale_validation_rejects_invalid_execution_shape() -> None:
    for milestones, partition_size in (((), 10), ((10, 10), 10), ((10,), 0)):
        try:
            run_unified_scale_validation(milestones, partition_size)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid scale validation input was accepted")
