from math import isclose

import pytest

from nollm.dream_geometry.geometry.chart import axial_to_world, make_hex_cell
from nollm.dream_geometry.geometry.coverage import CoverageDirection, MassConservationError, PartitionValidationError, ResidualReason, compute_distribution, compute_kernel
from nollm.dream_geometry.geometry.hexgrid import disk, nearest_axial
from nollm.dream_geometry.geometry.types import AxialCoord, LocalChart, Vec2


def test_dg1_cv_01_identical_control_weights_are_one() -> None:
    chart = LocalChart("same", 0, 1.0, 0.0, Vec2(0, 0))
    cell = make_hex_cell(chart, AxialCoord(0, 0))
    up = compute_kernel(cell, cell, CoverageDirection.fine_to_coarse)
    down = compute_kernel(cell, cell, CoverageDirection.coarse_to_fine)
    assert up.weight == 1.0
    assert down.weight == 1.0


def test_dg1_cv_02_same_overlap_has_different_directional_weights() -> None:
    fine = make_hex_cell(LocalChart("fine", 1, 0.5, 0.0, Vec2(0, 0)), AxialCoord(0, 0))
    coarse = make_hex_cell(LocalChart("coarse", 0, 1.0, 0.0, Vec2(0, 0)), AxialCoord(0, 0))
    up = compute_kernel(fine, coarse, CoverageDirection.fine_to_coarse)
    down = compute_kernel(coarse, fine, CoverageDirection.coarse_to_fine)
    assert isclose(up.overlap_area, down.overlap_area, rel_tol=1e-12, abs_tol=1e-12)
    assert up.weight != down.weight
    assert isclose(up.weight, 1.0, rel_tol=1e-12)
    assert isclose(down.weight, fine.area / coarse.area, rel_tol=1e-12)


def test_dg1_cv_03_fine_to_coarse_complete_partition_conserves_mass() -> None:
    fine_chart = LocalChart("fine", 1, 0.5, 0.0, Vec2(0, 0))
    coarse_chart = LocalChart("coarse", 0, 1.0, 0.0, Vec2(0, 0))
    source = make_hex_cell(fine_chart, AxialCoord(0, 0))
    targets = tuple(make_hex_cell(coarse_chart, axial) for axial in disk(AxialCoord(0, 0), 2))
    distribution = compute_distribution(source, targets, CoverageDirection.fine_to_coarse)
    assert isclose(sum(kernel.weight for kernel in distribution.kernels) + distribution.residual.mass, 1.0, abs_tol=1e-12)


def test_dg1_cv_04_coarse_to_fine_complete_partition_conserves_mass() -> None:
    coarse_chart = LocalChart("coarse", 0, 1.0, 0.0, Vec2(0, 0))
    fine_chart = LocalChart("fine", 1, 0.5, 0.0, Vec2(0, 0))
    source = make_hex_cell(coarse_chart, AxialCoord(0, 0))
    targets = tuple(make_hex_cell(fine_chart, axial) for axial in disk(AxialCoord(0, 0), 4))
    distribution = compute_distribution(source, targets, CoverageDirection.coarse_to_fine)
    assert isclose(sum(kernel.weight for kernel in distribution.kernels) + distribution.residual.mass, 1.0, abs_tol=1e-12)


def test_dg1_cv_05_incomplete_window_reports_outside_residual() -> None:
    source = make_hex_cell(LocalChart("fine", 1, 0.5, 0.0, Vec2(0, 0)), AxialCoord(0, 0))
    target = make_hex_cell(LocalChart("coarse", 0, 1.0, 0.0, Vec2(0.7, 0.0)), AxialCoord(0, 0))
    distribution = compute_distribution(source, (target,), CoverageDirection.fine_to_coarse)
    assert distribution.residual.mass > 0.0
    assert ResidualReason.outside_supplied_partition in distribution.residual.reasons


def test_dg1_cv_06_threshold_truncation_adds_residual_reason() -> None:
    source = make_hex_cell(LocalChart("fine", 2, 0.25, 0.4, Vec2(0.1, 0.2)), AxialCoord(0, 0))
    target_chart = LocalChart("coarse", 0, 1.0, 0.0, Vec2(0, 0))
    target_center = nearest_axial(target_chart, source.center)
    targets = tuple(make_hex_cell(target_chart, axial) for axial in disk(target_center, 2))
    distribution = compute_distribution(source, targets, CoverageDirection.fine_to_coarse, threshold=1.1)
    assert distribution.residual.mass > 0.0
    assert ResidualReason.threshold_truncation in distribution.residual.reasons


def test_dg1_cv_10_nearest_center_is_not_confirmed_coverage() -> None:
    source = make_hex_cell(LocalChart("fine", 1, 0.6, 0.45, Vec2(0.8, 0.0)), AxialCoord(0, 0))
    target_chart = LocalChart("coarse", 0, 1.0, 0.0, Vec2(0, 0))
    nearest = nearest_axial(target_chart, source.center)
    targets = tuple(make_hex_cell(target_chart, axial) for axial in disk(nearest, 1))
    weights = [compute_kernel(source, target, CoverageDirection.fine_to_coarse).weight for target in targets]
    assert len([weight for weight in weights if weight > 1e-12]) > 1


def test_dg1_cv_11_rotated_case_can_express_multitarget_coverage() -> None:
    source = make_hex_cell(LocalChart("fine", 1, 0.7, 0.7, Vec2(0.3, 0.2)), AxialCoord(0, 0))
    target_chart = LocalChart("coarse", 0, 1.0, 0.0, Vec2(0, 0))
    targets = tuple(make_hex_cell(target_chart, axial) for axial in disk(AxialCoord(0, 0), 2))
    distribution = compute_distribution(source, targets, CoverageDirection.fine_to_coarse)
    assert len(distribution.kernels) > 1


def test_dg1_cv_12_kernel_carries_direction_area_and_metadata() -> None:
    cell = make_hex_cell(LocalChart("same", 0, 1.0, 0.0, Vec2(0, 0)), AxialCoord(0, 0))
    kernel = compute_kernel(cell, cell, CoverageDirection.fine_to_coarse)
    assert kernel.direction is CoverageDirection.fine_to_coarse
    assert kernel.overlap_area == kernel.source_area == kernel.target_area
    assert kernel.metadata.numeric_mode == "float64_tolerance"


def test_dg1_1_cv_01_same_chart_id_different_translation_rejected() -> None:
    source = make_hex_cell(LocalChart("source", 0, 1.0, 0.0, Vec2(0, 0)), AxialCoord(0, 0))
    first = make_hex_cell(LocalChart("target", 0, 1.0, 0.0, Vec2(0, 0)), AxialCoord(0, 0))
    second = make_hex_cell(LocalChart("target", 0, 1.0, 0.0, Vec2(100, 0)), AxialCoord(10, 0))
    with pytest.raises(PartitionValidationError):
        compute_distribution(source, (first, second), CoverageDirection.fine_to_coarse)


def test_dg1_1_cv_02_same_chart_id_different_rotation_rejected() -> None:
    source = make_hex_cell(LocalChart("source", 0, 1.0, 0.0, Vec2(0, 0)), AxialCoord(0, 0))
    first = make_hex_cell(LocalChart("target", 0, 1.0, 0.0, Vec2(0, 0)), AxialCoord(0, 0))
    second = make_hex_cell(LocalChart("target", 0, 1.0, 0.5, Vec2(100, 0)), AxialCoord(10, 0))
    with pytest.raises(PartitionValidationError):
        compute_distribution(source, (first, second), CoverageDirection.fine_to_coarse)


def test_dg1_1_cv_03_same_geometry_nonoverlapping_targets_still_valid() -> None:
    source = make_hex_cell(LocalChart("source", 1, 0.5, 0.0, Vec2(0, 0)), AxialCoord(0, 0))
    chart = LocalChart("target", 0, 1.0, 0.0, Vec2(0, 0))
    first = make_hex_cell(chart, AxialCoord(0, 0))
    second = make_hex_cell(chart, AxialCoord(2, 0))
    distribution = compute_distribution(source, (first, second), CoverageDirection.fine_to_coarse)
    assert distribution.partition_size == 2
