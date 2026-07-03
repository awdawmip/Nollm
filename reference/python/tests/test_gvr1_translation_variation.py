from __future__ import annotations

import ast
import json
import sys
from math import isclose
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nollm.dream_geometry.geometry.metrics import distribution_metrics, summarize_distributions
from nollm.dream_geometry.geometry.schedules import DEFAULT_PHASE_SAMPLES, LAYER_PHASE_POLICIES, PARAMETER_MATRIX, ScaleRotationSchedule
from nollm.dream_geometry.geometry.types import AxialCoord, DEFAULT_TOLERANCE
from tests.fixtures.gvr1.fixture import (
    BASELINE_COMMIT,
    LAYER_GAPS,
    TRANSLATION_OFFSETS,
    all_finite,
    base_layers_for,
    baseline_parameter,
    build_metric_rows,
    canonical_metric_payload,
    distributions_for,
    distributions_for_offset,
    experiment_window_payload,
    independently_reconstruct_center_distributions,
    phase_label,
    phase_score_for,
    state_dirs,
)


def test_gvr1_01_experiment_window_and_sample_counts_are_fixed() -> None:
    rows = build_metric_rows()
    window = experiment_window_payload()

    assert baseline_parameter().parameter_id == "B"
    assert {parameter.parameter_id for parameter in PARAMETER_MATRIX if parameter.parameter_id == "B"} == {"B"}
    assert window["translation_offsets"] == tuple((offset.q, offset.r) for offset in TRANSLATION_OFFSETS)
    assert TRANSLATION_OFFSETS == (
        AxialCoord(-1, 0),
        AxialCoord(-1, 1),
        AxialCoord(0, -1),
        AxialCoord(0, 0),
        AxialCoord(0, 1),
        AxialCoord(1, -1),
        AxialCoord(1, 0),
    )
    assert {gap: base_layers_for(gap) for gap in LAYER_GAPS} == {
        1: tuple(range(0, 16)),
        2: tuple(range(0, 15)),
        4: tuple(range(0, 13)),
        8: tuple(range(0, 9)),
        16: (0,),
    }
    assert len(rows) == len(LAYER_GAPS) * len(DEFAULT_PHASE_SAMPLES) * len(LAYER_PHASE_POLICIES)
    assert all(row.parameter_id == "B" for row in rows)
    assert all(row.offset_count == 7 for row in rows)
    assert all(row.distribution_count == 7 * (17 - row.gap) for row in rows)
    assert {row.gap: row.distribution_count for row in rows if row.phase_label == "(0,0)" and row.phase_policy == "constant_local"} == {1: 112, 2: 105, 4: 91, 8: 63, 16: 7}
    assert all(all_finite(row) for row in rows)
    assert json.dumps(canonical_metric_payload(), sort_keys=True)


def test_gvr1_02_center_offset_reconstructs_gpr1_c1_baseline_b_inputs() -> None:
    schedule = ScaleRotationSchedule(baseline_parameter())
    for gap in LAYER_GAPS:
        for phase in DEFAULT_PHASE_SAMPLES:
            for policy in LAYER_PHASE_POLICIES:
                center = distributions_for_offset(schedule, gap, phase, policy, AxialCoord(0, 0))
                reconstructed = independently_reconstruct_center_distributions(gap, phase, policy)
                assert len(center) == len(reconstructed) == 17 - gap
                for left, right in zip(center, reconstructed):
                    assert len(left.kernels) == len(right.kernels)
                    assert left.residual.mass == right.residual.mass
                    assert tuple(kernel.weight for kernel in left.kernels) == tuple(kernel.weight for kernel in right.kernels)
                left_summary = summarize_distributions("B", gap, phase_label(phase), center, phase_score_for(schedule, gap, phase, policy))
                right_summary = summarize_distributions("B", gap, phase_label(phase), reconstructed, phase_score_for(schedule, gap, phase, policy))
                assert left_summary.branching_factors == right_summary.branching_factors
                assert left_summary.max_coverage_masses == right_summary.max_coverage_masses
                assert left_summary.repeat_overlap_entropy == right_summary.repeat_overlap_entropy
                assert left_summary.multi_layer_nesting_tendency == right_summary.multi_layer_nesting_tendency


def test_gvr1_03_translation_stencil_really_enters_coverage() -> None:
    schedule = ScaleRotationSchedule(baseline_parameter())
    phase = next(item for item in DEFAULT_PHASE_SAMPLES if item.phase_q == 0.5 and item.phase_r == 0.0)
    policy = next(item for item in LAYER_PHASE_POLICIES if item.policy_id == "layer_drift_control")
    per_offset = {offset: distributions_for_offset(schedule, 2, phase, policy, offset) for offset in TRANSLATION_OFFSETS}
    all_distributions = distributions_for(schedule, 2, phase, policy)
    row = next(row for row in build_metric_rows() if row.gap == 2 and row.phase_label == "(0.5,0)" and row.phase_policy == "layer_drift_control")

    assert len(base_layers_for(2)) == 15
    assert len(per_offset) == 7
    assert len(all_distributions) == 105
    assert all(len(distributions) == 15 for distributions in per_offset.values())
    assert row.distribution_count == 105
    assert row.offset_count == 7
    assert len({tuple(len(distribution.kernels) for distribution in distributions) for distributions in per_offset.values()}) > 1


def test_gvr1_04_variation_envelope_uses_actual_dg1_metrics() -> None:
    schedule = ScaleRotationSchedule(baseline_parameter())
    tolerance = DEFAULT_TOLERANCE.coordinate_abs_tol
    for row in build_metric_rows():
        phase = next(item for item in DEFAULT_PHASE_SAMPLES if phase_label(item) == row.phase_label)
        policy = next(item for item in LAYER_PHASE_POLICIES if item.policy_id == row.phase_policy)
        branching_means = []
        max_mass_means = []
        residual_means = []
        for offset in TRANSLATION_OFFSETS:
            metrics = tuple(distribution_metrics(distribution) for distribution in distributions_for_offset(schedule, row.gap, phase, policy, offset))
            branching_means.append(sum(metric.branching_factor for metric in metrics) / len(metrics))
            max_mass_means.append(sum(metric.max_coverage_mass for metric in metrics) / len(metrics))
            residual_means.append(sum(metric.residual_mass for metric in metrics) / len(metrics))
            assert all(0.0 <= metric.residual_mass <= 1.0 for metric in metrics)
        assert row.base_layer_count * row.offset_count == row.distribution_count
        assert row.envelope.branching_mean_min <= sum(branching_means) / len(branching_means) <= row.envelope.branching_mean_max
        assert row.envelope.max_mass_mean_min <= sum(max_mass_means) / len(max_mass_means) <= row.envelope.max_mass_mean_max
        assert row.envelope.residual_mean_min <= sum(residual_means) / len(residual_means) <= row.envelope.residual_mean_max
        assert isclose(row.envelope.branching_mean_span, max(branching_means) - min(branching_means), rel_tol=0.0, abs_tol=tolerance)
        assert isclose(row.envelope.max_mass_mean_span, max(max_mass_means) - min(max_mass_means), rel_tol=0.0, abs_tol=tolerance)
        assert isclose(row.envelope.residual_mean_span, max(residual_means) - min(residual_means), rel_tol=0.0, abs_tol=tolerance)


def test_gvr1_05_pure_geometry_fixture_does_not_touch_runtime_state(tmp_path) -> None:
    before = state_dirs(tmp_path)
    _ = canonical_metric_payload()
    after = state_dirs(tmp_path)

    assert before == after == {name: False for name in ("evidence", "capture", "cortex", "admission", "field", "assembly", "recall")}
    assert BASELINE_COMMIT == "c48ceba98e5d5197d16f91c3bad507b2ceaed242"
    _assert_no_forbidden_imports(Path("validation/gvr1/run_gvr1_translation_variation.py"))
    _assert_no_forbidden_imports(Path("reference/python/tests/fixtures/gvr1/fixture.py"))


def _assert_no_forbidden_imports(path: Path) -> None:
    forbidden = {
        "nollm.dream_geometry.evidence",
        "nollm.dream_geometry.capture",
        "nollm.dream_geometry.cortex",
        "nollm.dream_geometry.admission",
        "nollm.dream_geometry.assembly",
        "nollm.dream_geometry.recall",
        "nollm.dream_geometry.adapters",
        "nollm.dream_geometry.batch_admission",
        "socket",
        "requests",
        "urllib",
    }
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add("." * node.level + (node.module or ""))
    assert not (imports & forbidden)
