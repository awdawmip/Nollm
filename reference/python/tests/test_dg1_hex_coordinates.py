from math import isclose, pi, sqrt

import pytest

from nollm.dream_geometry.geometry.chart import axial_to_world, make_hex_cell, world_to_fractional_axial
from nollm.dream_geometry.geometry.hexgrid import axial_to_cube, cube_to_axial, disk, hex_distance, nearest_axial, neighbors, ring, round_fractional_axial
from nollm.dream_geometry.geometry.types import AxialCoord, CubeCoord, LocalChart, Vec2


def test_dg1_hx_01_axial_cube_round_trip() -> None:
    for axial in (AxialCoord(0, 0), AxialCoord(2, -3), AxialCoord(-4, 1)):
        assert cube_to_axial(axial_to_cube(axial)) == axial


def test_dg1_hx_02_cube_rejects_nonzero_sum() -> None:
    with pytest.raises(ValueError):
        CubeCoord(1, 1, 1)


def test_dg1_hx_03_neighbors_are_stable_distance_one() -> None:
    center = AxialCoord(0, 0)
    expected = (AxialCoord(1, 0), AxialCoord(0, 1), AxialCoord(-1, 1), AxialCoord(-1, 0), AxialCoord(0, -1), AxialCoord(1, -1))
    assert neighbors(center) == expected
    assert all(hex_distance(center, item) == 1 for item in neighbors(center))


def test_dg1_hx_04_ring_counts() -> None:
    for radius in (0, 1, 2, 5):
        expected = 1 if radius == 0 else 6 * radius
        assert len(ring(AxialCoord(0, 0), radius)) == expected


def test_dg1_hx_05_disk_counts() -> None:
    for radius in (0, 1, 2, 5):
        assert len(disk(AxialCoord(0, 0), radius)) == 1 + 3 * radius * (radius + 1)


def test_dg1_hx_06_hex_distance_matches_cube_max_formula() -> None:
    a = AxialCoord(2, -3)
    b = AxialCoord(-1, 4)
    ac = axial_to_cube(a)
    bc = axial_to_cube(b)
    assert hex_distance(a, b) == max(abs(ac.x - bc.x), abs(ac.y - bc.y), abs(ac.z - bc.z))


def test_dg1_hx_07_chart_round_trip_multiple_transforms() -> None:
    charts = (
        LocalChart("c0", 0, 1.0, 0.0, Vec2(0.0, 0.0)),
        LocalChart("c1", 1, 0.75, pi / 7.0, Vec2(2.5, -1.25)),
        LocalChart("c2", 2, 2.0, -pi / 5.0, Vec2(-3.0, 4.0)),
    )
    for chart in charts:
        for axial in (AxialCoord(0, 0), AxialCoord(1, -2), AxialCoord(-3, 1)):
            point = axial_to_world(chart, axial)
            qf, rf = world_to_fractional_axial(chart, point)
            assert isclose(qf, axial.q, abs_tol=1e-12)
            assert isclose(rf, axial.r, abs_tol=1e-12)
            assert nearest_axial(chart, point) == axial


def test_dg1_hx_08_round_tie_policy_is_stable() -> None:
    first = round_fractional_axial(0.5, 0.0)
    second = round_fractional_axial(0.5, 0.0)
    assert first == second
    with pytest.raises(ValueError):
        round_fractional_axial(0.5, 0.0, tie_policy="bankers")


def test_dg1_hx_09_adjacent_center_distance_is_sqrt3_times_side_length() -> None:
    chart = LocalChart("c", 0, 2.0, 0.0, Vec2(0.0, 0.0))
    center = axial_to_world(chart, AxialCoord(0, 0))
    for neighbor in neighbors(AxialCoord(0, 0)):
        distance = (axial_to_world(chart, neighbor) - center).norm()
        assert isclose(distance, sqrt(3.0) * chart.side_length, rel_tol=1e-12, abs_tol=1e-12)
