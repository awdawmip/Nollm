from math import isclose, pi

from nollm.dream_geometry.geometry.chart import make_hex_cell, normalized_phase, phase_distance
from nollm.dream_geometry.geometry.polygon import polygon_area
from nollm.dream_geometry.geometry.types import AxialCoord, LocalChart, PhaseCoord, Vec2


def test_local_chart_make_hex_cell_has_stable_identity_and_area() -> None:
    chart = LocalChart("chart_a", 3, 1.25, pi / 8.0, Vec2(3.0, -2.0), {"purpose": "test"})
    cell = make_hex_cell(chart, AxialCoord(2, -1))
    assert cell.cell_ref.chart_id == "chart_a"
    assert cell.cell_ref.axial == AxialCoord(2, -1)
    assert len(cell.vertices) == 6
    assert isclose(polygon_area(cell.vertices), cell.area, rel_tol=1e-12, abs_tol=1e-12)


def test_normalized_phase_is_torus_canonical() -> None:
    chart_a = LocalChart("a", 0, 1.0, 0.0, Vec2(0.0, 0.0))
    chart_b = LocalChart("b", 0, 1.0, 0.0, Vec2(3.0 ** 0.5, 0.0))
    assert normalized_phase(chart_a) == PhaseCoord(0.0, 0.0)
    assert normalized_phase(chart_b) == PhaseCoord(0.0, 0.0)


def test_phase_distance_wraps_near_zero_one_boundary() -> None:
    a = PhaseCoord(0.99, 0.01)
    b = PhaseCoord(0.01, 0.99)
    assert isclose(phase_distance(a, b), (0.02**2 + 0.02**2) ** 0.5, rel_tol=1e-12)
