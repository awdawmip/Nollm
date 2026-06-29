from math import isclose

from nollm.dream_geometry.geometry.chart import normalized_phase, phase_distance, relative_phase
from nollm.dream_geometry.geometry.coverage import CoverageDirection, compute_distribution
from nollm.dream_geometry.geometry.hexgrid import disk, nearest_axial
from nollm.dream_geometry.geometry.metrics import effective_parent_count, multi_layer_nesting_tendency, phase_recurrence_score, repeat_overlap_entropy, summarize_distributions
from nollm.dream_geometry.geometry.schedules import DEFAULT_PHASE_SAMPLES, PARAMETER_MATRIX, PhaseSchedule, ScaleRotationSchedule
from nollm.dream_geometry.geometry.types import AxialCoord, PhaseCoord
from nollm.dream_geometry.geometry.chart import make_hex_cell
from nollm.dream_geometry.validation.dg1_baseline_report import _phase_score_for


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


def test_dg1_1_ar_01_relative_phase_changes_with_translation() -> None:
    source = ScaleRotationSchedule(PARAMETER_MATRIX[0]).chart_for_layer(0, PhaseSchedule(0.0, 0.0))
    first = ScaleRotationSchedule(PARAMETER_MATRIX[0]).chart_for_layer(1, PhaseSchedule(0.0, 0.0))
    second = ScaleRotationSchedule(PARAMETER_MATRIX[0]).chart_for_layer(1, PhaseSchedule(0.5, 0.0))
    assert relative_phase(source, first) != relative_phase(source, second)


def test_dg1_1_ar_02_relative_phase_is_not_local_phase_echo() -> None:
    schedule = ScaleRotationSchedule(PARAMETER_MATRIX[1])
    phase = PhaseSchedule(0.5, 0.0)
    local = normalized_phase(schedule.chart_for_layer(8, phase))
    relative = relative_phase(schedule.chart_for_layer(0, phase), schedule.chart_for_layer(8, phase))
    assert relative != local


def test_dg1_1_ar_03_phase_recurrence_score_can_distinguish_samples() -> None:
    repeated = (PhaseCoord(0.0, 0.0), PhaseCoord(0.0, 0.0), PhaseCoord(0.0, 0.0))
    varied = (PhaseCoord(0.0, 0.0), PhaseCoord(0.25, 0.0), PhaseCoord(0.5, 0.0))
    assert phase_recurrence_score(repeated) > phase_recurrence_score(varied)


def test_dg1_1_ar_04_baseline_b_gap8_and_gap16_rotation_recurrence_remain() -> None:
    baseline = next(item for item in PARAMETER_MATRIX if item.parameter_id == "B")
    assert (baseline.delta_theta_degrees * 8) % 60.0 == 0.0
    assert (baseline.delta_theta_degrees * 16) % 60.0 == 0.0


def test_dg1_1_ar_05_report_phase_score_is_not_globally_constant() -> None:
    scores = {
        _phase_score_for(ScaleRotationSchedule(parameter), gap, phase)
        for parameter in PARAMETER_MATRIX
        for gap in (1, 2, 4, 8, 16)
        for phase in DEFAULT_PHASE_SAMPLES
    }
    assert len(scores) > 1
