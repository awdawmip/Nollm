from math import isclose, pi, sqrt
from random import Random

from nollm.dream_geometry.geometry.chart import make_hex_cell
from nollm.dream_geometry.geometry.hexgrid import neighbors
from nollm.dream_geometry.geometry.polygon import circumcircle_candidate_may_overlap, convex_polygon_intersection_area, polygon_area
from nollm.dream_geometry.geometry.types import AxialCoord, LocalChart, Vec2


def chart() -> LocalChart:
    return LocalChart("pg", 0, 1.0, 0.0, Vec2(0.0, 0.0))


def test_dg1_pg_01_regular_hex_area() -> None:
    cell = make_hex_cell(chart(), AxialCoord(0, 0))
    assert isclose(polygon_area(cell.vertices), 3.0 * sqrt(3.0) / 2.0, rel_tol=1e-12)


def test_dg1_pg_02_identical_intersection_area() -> None:
    cell = make_hex_cell(chart(), AxialCoord(0, 0))
    assert isclose(convex_polygon_intersection_area(cell.vertices, cell.vertices), cell.area, rel_tol=1e-12)


def test_dg1_pg_03_adjacent_hexes_share_boundary_only() -> None:
    a = make_hex_cell(chart(), AxialCoord(0, 0))
    for axial in neighbors(AxialCoord(0, 0)):
        b = make_hex_cell(chart(), axial)
        assert convex_polygon_intersection_area(a.vertices, b.vertices) == 0.0


def test_dg1_pg_04_vertex_touch_area_is_zero() -> None:
    a = make_hex_cell(chart(), AxialCoord(0, 0))
    b = make_hex_cell(chart(), AxialCoord(1, 1))
    assert convex_polygon_intersection_area(a.vertices, b.vertices) == 0.0


def test_dg1_pg_05_disjoint_area_is_zero() -> None:
    a = make_hex_cell(chart(), AxialCoord(0, 0))
    b = make_hex_cell(chart(), AxialCoord(8, -8))
    assert convex_polygon_intersection_area(a.vertices, b.vertices) == 0.0


def test_dg1_pg_06_contained_intersection_is_smaller_area() -> None:
    outer = make_hex_cell(LocalChart("outer", 0, 2.0, 0.0, Vec2(0.0, 0.0)), AxialCoord(0, 0))
    inner = make_hex_cell(LocalChart("inner", 1, 0.5, 0.0, Vec2(0.0, 0.0)), AxialCoord(0, 0))
    assert isclose(convex_polygon_intersection_area(outer.vertices, inner.vertices), inner.area, rel_tol=1e-12)


def test_dg1_pg_07_fixed_random_hex_pairs_are_symmetric_and_bounded() -> None:
    rng = Random(47)
    for index in range(20):
        a_chart = LocalChart(f"a{index}", 0, rng.uniform(0.4, 1.8), rng.uniform(-pi, pi), Vec2(rng.uniform(-1, 1), rng.uniform(-1, 1)))
        b_chart = LocalChart(f"b{index}", 0, rng.uniform(0.4, 1.8), rng.uniform(-pi, pi), Vec2(rng.uniform(-1, 1), rng.uniform(-1, 1)))
        a = make_hex_cell(a_chart, AxialCoord(0, 0))
        b = make_hex_cell(b_chart, AxialCoord(0, 0))
        ab = convex_polygon_intersection_area(a.vertices, b.vertices)
        ba = convex_polygon_intersection_area(b.vertices, a.vertices)
        assert isclose(ab, ba, rel_tol=1e-12, abs_tol=1e-12)
        assert 0.0 <= ab <= min(a.area, b.area) + 1e-12


def test_dg1_pg_08_degenerate_duplicate_vertices_do_not_create_positive_area() -> None:
    cell = make_hex_cell(chart(), AxialCoord(0, 0))
    duplicate = tuple(list(cell.vertices) + [cell.vertices[-1]])
    assert polygon_area(duplicate) > 0.0
    far = make_hex_cell(chart(), AxialCoord(10, 0))
    assert convex_polygon_intersection_area(duplicate, far.vertices) == 0.0


def test_dg1_pg_09_circumcircle_false_implies_zero_area() -> None:
    a = make_hex_cell(chart(), AxialCoord(0, 0))
    b = make_hex_cell(chart(), AxialCoord(8, 0))
    assert circumcircle_candidate_may_overlap(a, b) is False
    assert convex_polygon_intersection_area(a.vertices, b.vertices) == 0.0
