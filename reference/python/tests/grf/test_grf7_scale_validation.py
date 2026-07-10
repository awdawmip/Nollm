from __future__ import annotations

from nollm.grf.grf7_scale_validation import run_grf7_global_scale_validation, run_grf7_scale_validation


def test_grf7_scale_validation_separates_resident_global_and_resource_units(tmp_path) -> None:
    result = run_grf7_scale_validation(tmp_path, (100, 250, 500), 1_000, 250)
    assert tuple(item.placement_count for item in result.resident) == (100, 250, 500)
    assert result.resident[-1].source_fallback_success == "500/500"
    assert result.resident[-1].process_peak_rss_bytes > 0
    assert result.resident[-1].python_deep_estimate_bytes > result.resident[-1].shallow_estimate_bytes
    assert result.global_sharded.logical_global_placement_count == 1_000
    assert result.global_sharded.partition_count == 4
    assert result.global_sharded.loaded_partition_count == 0
    assert result.global_sharded.generated_evidence_count == 1_000
    assert result.global_sharded.source_fallback_success == "1000/1000"
    assert result.global_sharded.reloaded_placement_count == 1_000
    assert result.global_sharded.serialized_disk_bytes > 0
    assert result.global_sharded.file_count >= 15
    assert result.status == "GATE_D_PASS|GATE_E_PASS"


def test_global_only_scale_reports_stage_local_rss(tmp_path) -> None:
    metric = run_grf7_global_scale_validation(tmp_path, 500, 250)
    assert metric.logical_global_placement_count == 500
    assert metric.process_peak_rss_bytes > 0
    assert metric.reloaded_placement_count == 500
