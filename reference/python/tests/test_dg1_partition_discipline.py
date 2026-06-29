import pytest

from nollm.dream_geometry.geometry.coverage import CoverageDirection, MassConservationError, PartitionValidationError, compute_distribution, validate_nonoverlapping_partition
from nollm.dream_geometry.geometry.types import AxialCoord, HexCell, LocalChart, Vec2
from nollm.dream_geometry.geometry.chart import make_hex_cell


def test_dg1_cv_07_overlapping_targets_fail_partition_validation() -> None:
    chart = LocalChart("targets", 0, 1.0, 0.0, Vec2(0, 0))
    first = make_hex_cell(chart, AxialCoord(0, 0))
    shifted = make_hex_cell(LocalChart("targets", 0, 1.0, 0.0, Vec2(0.5, 0.0)), AxialCoord(0, 0))
    with pytest.raises(PartitionValidationError):
        validate_nonoverlapping_partition((first, shifted))


def test_dg1_cv_08_overlapping_chart_targets_are_not_conserved_distribution() -> None:
    source = make_hex_cell(LocalChart("source", 0, 1.0, 0.0, Vec2(0, 0)), AxialCoord(0, 0))
    target_a = make_hex_cell(LocalChart("target_a", 0, 1.0, 0.0, Vec2(0, 0)), AxialCoord(0, 0))
    target_b = make_hex_cell(LocalChart("target_b", 0, 1.0, 0.0, Vec2(0, 0)), AxialCoord(0, 0))
    with pytest.raises(PartitionValidationError):
        compute_distribution(source, (target_a, target_b), CoverageDirection.fine_to_coarse)


def test_dg1_cv_09_mass_over_one_raises_when_detected(monkeypatch) -> None:
    import nollm.dream_geometry.geometry.coverage as coverage

    source = make_hex_cell(LocalChart("source", 0, 1.0, 0.0, Vec2(0, 0)), AxialCoord(0, 0))
    target = make_hex_cell(LocalChart("target", 0, 1.0, 0.0, Vec2(0, 0)), AxialCoord(0, 0))
    real_kernel = coverage.compute_kernel(source, target, CoverageDirection.fine_to_coarse)

    def fake_kernel(*_args, **_kwargs):
        return coverage.CoverageKernel(
            real_kernel.source_cell,
            real_kernel.target_cell,
            real_kernel.direction,
            real_kernel.overlap_area,
            real_kernel.source_area,
            real_kernel.target_area,
            1.5,
            real_kernel.metadata,
        )

    monkeypatch.setattr(coverage, "validate_nonoverlapping_partition", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(coverage, "compute_kernel", fake_kernel)
    with pytest.raises(MassConservationError):
        coverage.compute_distribution(source, (target,), CoverageDirection.fine_to_coarse)
