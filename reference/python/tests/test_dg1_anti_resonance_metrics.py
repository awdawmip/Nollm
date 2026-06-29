from math import isclose

from nollm.dream_geometry.geometry.chart import normalized_phase, phase_distance
from nollm.dream_geometry.geometry.coverage import CoverageDirection, compute_distribution
from nollm.dream_geometry.geometry.hexgrid import disk, nearest_axial
from nollm.dream_geometry.geometry.metrics import effective_parent_count, multi_layer_nesting_tendency, repeat_overlap_entropy, summarize_distributions
from nollm.dream_geometry.geometry.schedules import DEFAULT_PHASE_SAMPLES, PARAMETER_MATRIX, PhaseSchedule, ScaleRotationSchedule
from nollm.dream_geometry.geometry.types import AxialCoord, PhaseCoord
from nollm.dream_geometry.geometry.chart import make_hex_cell


def test_dg1_ar_01_baseline_b_gap8_rotation_recurrence_mod_60() -> None:
    baseline = next(item for item in PARAMETER_MATRIX if item.parameter_id == "B")
    assert (baseline.delta_theta_degrees * 8) % 60.0 == 0.0


def test_dg1_ar_02_baseline_b_gap8_side_ratio_is_one_quarter() -> None:
    baseline = ScaleRotationSchedule(next(item for item in PARAMETER_MATRIX if item.parameter_id == "B"))
    assert isclose(baseline.side_length(8) / baseline.side_length(0), 0.25, rel_tol=1e-12)


def test_dg1_ar_03_parameter_matrix_constructs_layers_0_to_32() -> None:
    for parameter in PARAMETER_MATRIX:
        schedule = ScaleRotationSchedule(parameter)
        assert len([schedule.side_length(layer) for layer in range(33)]) == 33


def test_dg1_ar_04_branching_factor_is_finite_for_fixed_window() -> None:
    schedule = ScaleRotationSchedule(PARAMETER_MATRIX[0])
    source_chart = schedule.chart_for_layer(2, DEFAULT_PHASE_SAMPLES[0])
    target_chart = schedule.chart_for_layer(0, DEFAULT_PHASE_SAMPLES[0])
    source = make_hex_cell(source_chart, AxialCoord(0, 0))
    target_center = nearest_axial(target_chart, source.center)
    targets = tuple(make_hex_cell(target_chart, axial) for axial in disk(target_center, 3))
    distribution = compute_distribution(source, targets, CoverageDirection.fine_to_coarse)
    assert 0 < len(distribution.kernels) < len(targets)


def test_dg1_ar_05_effective_count_distinguishes_single_and_split_mass() -> None:
    assert effective_parent_count((1.0,)) == 1.0
    assert isclose(effective_parent_count((0.5, 0.5)), 2.0, rel_tol=1e-12)


def test_dg1_ar_06_phase_distance_wraps_torus_boundary() -> None:
    assert isclose(phase_distance(PhaseCoord(0.99, 0.99), PhaseCoord(0.01, 0.01)), (0.02**2 + 0.02**2) ** 0.5, rel_tol=1e-12)


def test_dg1_ar_07_metrics_are_reproducible() -> None:
    assert repeat_overlap_entropy(((1, 2), (1, 2), (2, 1))) == repeat_overlap_entropy(((1, 2), (1, 2), (2, 1)))
    assert multi_layer_nesting_tendency((1.0, 0.7, 0.999999999)) == multi_layer_nesting_tendency((1.0, 0.7, 0.999999999))


def test_dg1_ar_08_phase_sample_changes_values_not_definitions() -> None:
    schedule = ScaleRotationSchedule(PARAMETER_MATRIX[1])
    first = normalized_phase(schedule.chart_for_layer(8, PhaseSchedule(0.0, 0.0)))
    second = normalized_phase(schedule.chart_for_layer(8, PhaseSchedule(0.5, 0.0)))
    assert first != second
    assert hasattr(first, "q") and hasattr(second, "r")
