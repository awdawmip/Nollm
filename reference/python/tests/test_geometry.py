from __future__ import annotations

import ast
from math import atan2, degrees, hypot, sqrt
from pathlib import Path
import unittest

from nollm.geometry import (
    Axial,
    Cube,
    HexAddress,
    LayerSpec,
    LocalChart,
    SimilarityTransform,
    axial_distance,
    axial_disk,
    axial_neighbor,
    axial_ring,
    axial_to_world,
    coverage_map,
    coverage_weight,
    default_layer_specs,
    hex_polygon,
    hex_cell_polygon,
    hex_overlap,
    polygon_area,
    polygon_intersection_area,
    regular_hex_area,
    similarity_from_two_points,
    world_to_axial,
)


ROOT = Path(__file__).resolve().parents[3]
GEOMETRY_SOURCE = ROOT / "reference" / "python" / "nollm" / "geometry.py"


class GeometryCoordinateTests(unittest.TestCase):
    def test_axial_cube_roundtrip(self) -> None:
        self.assertEqual(Axial(3, -5).to_cube().to_axial(), Axial(3, -5))

    def test_invalid_cube_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Cube(1, 1, 1)

    def test_neighbors_distance_ring_and_disk(self) -> None:
        self.assertEqual(axial_neighbor(Axial(0, 0), 0), Axial(1, 0))
        self.assertEqual(axial_distance(Axial(0, 0), Axial(1, 0)), 1)
        self.assertEqual(axial_distance(Axial(1, 0), Axial(0, 0)), 1)
        self.assertEqual(len(axial_ring(Axial(0, 0), 0)), 1)
        self.assertEqual(len(axial_ring(Axial(0, 0), 2)), 12)
        self.assertEqual(len(axial_disk(Axial(0, 0), 3)), 37)

    def test_invalid_radius_is_rejected(self) -> None:
        for radius in (-1, True):
            with self.assertRaises(ValueError):
                axial_ring(Axial(0, 0), radius)  # type: ignore[arg-type]
            with self.assertRaises(ValueError):
                axial_disk(Axial(0, 0), radius)  # type: ignore[arg-type]


class GeometryLayerTests(unittest.TestCase):
    def test_layer_defaults_match_dream_geometry_policy(self) -> None:
        self.assertEqual(LayerSpec(layer=0).orientation, "pointy")
        self.assertAlmostEqual(
            LayerSpec(layer=1, s0=1.0, beta=2 ** 0.25).side_length,
            2 ** -0.25,
        )
        self.assertAlmostEqual(LayerSpec(layer=8, theta_deg=22.5).rotation_deg, 0.0)

    def test_world_axial_roundtrip_with_rotation(self) -> None:
        layer = LayerSpec(
            layer=3,
            origin=(10.0, -4.0),
            translation=(0.25, 0.5),
        )
        cell = Axial(-2, 4)
        self.assertEqual(world_to_axial(axial_to_world(cell, layer), layer), cell)

    def test_world_axial_roundtrip_for_pointy_and_flat_orientation(self) -> None:
        for orientation in ("pointy", "flat"):
            with self.subTest(orientation=orientation):
                layer = LayerSpec(
                    layer=2,
                    origin=(4.0, -2.0),
                    translation=(0.5, 1.25),
                    orientation=orientation,
                )
                for cell in (Axial(0, 0), Axial(2, -1), Axial(-3, 4)):
                    self.assertEqual(world_to_axial(axial_to_world(cell, layer), layer), cell)

    def test_first_ring_center_spacing_is_strict_model_t_for_pointy_and_flat(self) -> None:
        side_length = 2.5
        expected_spacing = sqrt(3) * side_length
        for orientation in ("pointy", "flat"):
            with self.subTest(orientation=orientation):
                layer = LayerSpec(layer=0, s0=side_length, orientation=orientation)
                center = axial_to_world(Axial(0, 0), layer)
                for neighbor in axial_ring(Axial(0, 0), 1):
                    point = axial_to_world(neighbor, layer)
                    self.assertAlmostEqual(_distance(center, point), expected_spacing)
                    self.assertNotAlmostEqual(_distance(center, point), side_length)

    def test_layer_spec_rejects_invalid_parameters(self) -> None:
        invalid_kwargs = [
            {"layer": -1},
            {"layer": True},
            {"s0": 0.0},
            {"s0": -1.0},
            {"beta": 0.0},
            {"beta": -1.0},
            {"rotation_mod_deg": 0.0},
            {"rotation_mod_deg": -60.0},
            {"orientation": "diagonal"},
            {"origin": [0.0, 0.0]},
            {"origin": (0.0, True)},
            {"translation": (0.0,)},
        ]
        for kwargs in invalid_kwargs:
            with self.subTest(kwargs=kwargs):
                params = {"layer": 0}
                params.update(kwargs)
                with self.assertRaises(ValueError):
                    LayerSpec(**params)

    def test_alternative_parameter_regimes_remain_supported(self) -> None:
        regimes = [
            (2 ** 0.25, 15.0),
            (2 ** 0.25, 22.5),
            (sqrt(2), 15.0),
            ((1 + sqrt(5)) / 2, 15.0),
            (sqrt(3), 30.0),
        ]
        source = HexAddress(0, 0, 0)
        for beta, theta_deg in regimes:
            with self.subTest(beta=beta, theta_deg=theta_deg):
                layer0 = LayerSpec(layer=0, beta=beta, theta_deg=theta_deg)
                layer1 = LayerSpec(layer=1, beta=beta, theta_deg=theta_deg)
                polygon = hex_cell_polygon(Axial(0, 0), layer1)
                self.assertGreater(polygon_area(polygon), 0.0)
                self.assertGreater(len(coverage_map(source, layer0, layer1, search_radius=3)), 0)


class GeometryPolygonTests(unittest.TestCase):
    def test_regular_hex_area_formula(self) -> None:
        self.assertAlmostEqual(regular_hex_area(2.0), 3 * sqrt(3) / 2 * 4)

    def test_hex_area_and_polygon_reject_non_positive_side_length(self) -> None:
        for side_length in (0.0, -1.0, True):
            with self.subTest(side_length=side_length):
                with self.assertRaises(ValueError):
                    regular_hex_area(side_length)  # type: ignore[arg-type]
                with self.assertRaises(ValueError):
                    hex_polygon((0.0, 0.0), side_length)  # type: ignore[arg-type]

    def test_hex_polygon_rejects_invalid_orientation(self) -> None:
        with self.assertRaises(ValueError):
            hex_polygon((0.0, 0.0), 1.0, orientation="diagonal")  # type: ignore[arg-type]

    def test_pointy_and_flat_vertex_conventions_are_explicit(self) -> None:
        rotation_deg = 17.0
        rotation_rad = rotation_deg * 3.141592653589793 / 180.0
        pointy = hex_polygon((0.0, 0.0), 1.0, rotation_rad, orientation="pointy")
        flat = hex_polygon((0.0, 0.0), 1.0, rotation_rad, orientation="flat")

        self.assertAlmostEqual(_vertex_angle_deg(pointy[0]), rotation_deg + 30.0)
        self.assertAlmostEqual(_vertex_angle_deg(flat[0]), rotation_deg)

    def test_hex_cell_polygon_uses_layer_orientation_without_mixing_conventions(self) -> None:
        cell = Axial(0, 0)
        pointy_layer = LayerSpec(layer=0, orientation="pointy")
        flat_layer = LayerSpec(layer=0, orientation="flat")
        pointy_polygon = hex_cell_polygon(cell, pointy_layer)
        flat_polygon = hex_cell_polygon(cell, flat_layer)

        self.assertAlmostEqual(polygon_area(pointy_polygon), pointy_layer.area)
        self.assertAlmostEqual(polygon_area(flat_polygon), flat_layer.area)
        self.assertAlmostEqual(_vertex_angle_deg(pointy_polygon[0]), 30.0)
        self.assertAlmostEqual(_vertex_angle_deg(flat_polygon[0]), 0.0)
        self.assertNotEqual(pointy_polygon[0], flat_polygon[0])

    def test_hex_intersection_area_for_same_and_disjoint_cells(self) -> None:
        layer = LayerSpec(layer=0)
        poly = hex_cell_polygon(Axial(0, 0), layer)
        self.assertAlmostEqual(polygon_intersection_area(poly, poly), layer.area)

        far = hex_cell_polygon(Axial(20, 20), layer)
        self.assertAlmostEqual(polygon_intersection_area(poly, far), 0.0)

    def test_polygon_intersection_area_is_symmetric(self) -> None:
        layer = LayerSpec(layer=0)
        first = hex_cell_polygon(Axial(0, 0), layer)
        second = hex_cell_polygon(Axial(1, 0), layer)
        self.assertAlmostEqual(
            polygon_intersection_area(first, second),
            polygon_intersection_area(second, first),
        )


class GeometryCoverageTests(unittest.TestCase):
    def test_same_layer_same_hex_has_full_weights(self) -> None:
        layer = LayerSpec(layer=0)
        cell = HexAddress(0, 0, 0)
        coverage = hex_overlap(cell, layer, cell, layer)
        self.assertAlmostEqual(coverage.weight_source, 1.0)
        self.assertAlmostEqual(coverage.weight_target, 1.0)
        self.assertAlmostEqual(coverage.source_share, coverage.weight_source)
        self.assertAlmostEqual(coverage.target_share, coverage.weight_target)
        self.assertAlmostEqual(coverage.jaccard, 1.0)

    def test_far_hex_has_no_intersection(self) -> None:
        layer = LayerSpec(layer=0)
        coverage = hex_overlap(
            HexAddress(0, 0, 0),
            layer,
            HexAddress(0, 20, 20),
            layer,
        )
        self.assertAlmostEqual(coverage.intersection_area, 0.0)

    def test_cross_layer_coverage_is_many_to_many_overlap(self) -> None:
        source = HexAddress(0, 0, 0)
        result = coverage_map(source, LayerSpec(layer=0), LayerSpec(layer=1), search_radius=3)
        self.assertGreater(len(result), 1)
        self.assertFalse(hasattr(result[0], "parent"))
        for forbidden_attr in ("children", "owner", "folder", "belongs_to"):
            self.assertFalse(hasattr(result[0], forbidden_attr))
        self.assertTrue(0.98 <= sum(item.weight_source for item in result) <= 1.02)

    def test_coverage_helpers_reject_invalid_inputs(self) -> None:
        layer = LayerSpec(layer=0)
        coverage = hex_overlap(HexAddress(0, 0, 0), layer, HexAddress(0, 0, 0), layer)
        with self.assertRaises(ValueError):
            coverage_weight(coverage, "unsupported")  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            coverage_map(HexAddress(0, 0, 0), layer, layer, search_radius=-1)
        with self.assertRaises(ValueError):
            coverage_map(HexAddress(0, 0, 0), layer, layer, search_radius=True)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            coverage_map(HexAddress(0, 0, 0), layer, layer, min_weight=-0.1)

    def test_coverage_map_returns_only_positive_overlap_items_by_default(self) -> None:
        result = coverage_map(HexAddress(0, 0, 0), LayerSpec(layer=0), LayerSpec(layer=1), search_radius=3)
        self.assertTrue(all(item.intersection_area > 0 for item in result))

    def test_exact_containment_uses_target_share_not_source_share(self) -> None:
        source = HexAddress(0, 0, 0)
        rows = coverage_map(source, LayerSpec(layer=0), LayerSpec(layer=1), search_radius=3)
        exact = [row for row in rows if _almost_equal(row.target_share, 1.0)]

        self.assertEqual(len(exact), 1)
        self.assertEqual(exact[0].target, HexAddress(1, 0, 0))
        self.assertNotAlmostEqual(exact[0].source_share, 1.0)

    def test_a_profile_one_step_template_uses_strict_model_t(self) -> None:
        rows = coverage_map(
            HexAddress(0, 0, 0),
            LayerSpec(layer=0, beta=sqrt(2), theta_deg=15.0),
            LayerSpec(layer=1, beta=sqrt(2), theta_deg=15.0),
            search_radius=4,
        )

        self.assertEqual(len(rows), 7)
        self.assertAlmostEqual(sum(row.source_share for row in rows), 1.0)
        center = _coverage_for_target(rows, HexAddress(1, 0, 0))
        outer = [row for row in rows if row.target != HexAddress(1, 0, 0)]
        self.assertAlmostEqual(center.source_share, 0.5)
        self.assertTrue(all(_almost_equal(row.source_share, 1.0 / 12.0) for row in outer))
        self.assertEqual(sum(1 for row in rows if _almost_equal(row.target_share, 1.0)), 1)

    def test_b_profile_one_step_template_uses_strict_model_t(self) -> None:
        rows = coverage_map(
            HexAddress(0, 0, 0),
            LayerSpec(layer=0, beta=2 ** 0.25, theta_deg=22.5),
            LayerSpec(layer=1, beta=2 ** 0.25, theta_deg=22.5),
            search_radius=4,
        )

        self.assertEqual(len(rows), 7)
        self.assertAlmostEqual(sum(row.source_share for row in rows), 1.0)
        center = _coverage_for_target(rows, HexAddress(1, 0, 0))
        outer = [row for row in rows if row.target != HexAddress(1, 0, 0)]
        self.assertAlmostEqual(center.source_share, 1.0 / sqrt(2))
        self.assertTrue(all(_almost_equal(row.source_share, (2.0 - sqrt(2)) / 12.0) for row in outer))
        self.assertEqual(sum(1 for row in rows if _almost_equal(row.target_share, 1.0)), 1)


class GeometryLocalChartTests(unittest.TestCase):
    def test_local_chart_projects_bounded_seed_disk(self) -> None:
        chart = LocalChart(
            seed=HexAddress(0, 0, 0),
            layer_specs=default_layer_specs(2),
            source_radius=1,
            projection_radius=3,
        )
        self.assertEqual(len(chart.cells_on_seed_layer()), 7)
        projection = chart.project_seed_layer_to(1)
        self.assertEqual(len(projection), 7)
        self.assertTrue(all(len(items) > 0 for items in projection.values()))

    def test_local_chart_rejects_missing_layer_specs(self) -> None:
        chart = LocalChart(
            seed=HexAddress(0, 0, 0),
            layer_specs={0: LayerSpec(layer=0)},
        )
        with self.assertRaisesRegex(ValueError, "missing layer spec"):
            chart.project_seed_layer_to(1)


class GeometrySimilarityTests(unittest.TestCase):
    def assertPointAlmostEqual(self, actual: tuple[float, float], expected: tuple[float, float]) -> None:
        self.assertAlmostEqual(actual[0], expected[0])
        self.assertAlmostEqual(actual[1], expected[1])

    def test_inverse_roundtrip(self) -> None:
        transform = SimilarityTransform(scale=2.5, rotation_rad=0.75, translation=(3.0, -2.0))
        point = (4.0, -1.5)
        self.assertPointAlmostEqual(transform.inverse().apply(transform.apply(point)), point)

    def test_compose_applies_self_then_after(self) -> None:
        first = SimilarityTransform(scale=2.0, rotation_rad=0.25, translation=(1.0, 3.0))
        after = SimilarityTransform(scale=0.5, rotation_rad=-0.5, translation=(-4.0, 2.0))
        point = (5.0, -2.0)
        self.assertPointAlmostEqual(first.compose(after).apply(point), after.apply(first.apply(point)))

    def test_similarity_from_two_points_maps_both_points(self) -> None:
        built = similarity_from_two_points((0, 0), (1, 0), (10, 10), (10, 12))
        self.assertAlmostEqual(built.transform.scale, 2.0)
        self.assertPointAlmostEqual(built.transform.apply((0, 0)), (10, 10))
        self.assertPointAlmostEqual(built.transform.apply((1, 0)), (10, 12))
        self.assertAlmostEqual(built.residual, 0.0)

    def test_invalid_similarity_inputs_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            similarity_from_two_points((0, 0), (0, 0), (1, 1), (2, 2))
        with self.assertRaises(ValueError):
            SimilarityTransform(scale=0).inverse()


class GeometryBoundaryTests(unittest.TestCase):
    def test_geometry_module_does_not_import_runtime_or_card_writing_layers(self) -> None:
        tree = ast.parse(GEOMETRY_SOURCE.read_text(encoding="utf-8"))
        imported_modules: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module.split(".")[0])

        forbidden = {
            "annotation",
            "audit",
            "cli",
            "filesystem",
            "history",
            "models",
            "recall",
            "review",
            "tool_api",
            "validation",
        }
        self.assertTrue(imported_modules.isdisjoint(forbidden))

    def test_policy_docs_allow_only_d1_pure_polygon_overlap(self) -> None:
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        d1_doc = (ROOT / "docs" / "geometry" / "D1_PURE_GEOMETRY_KERNEL.md").read_text(
            encoding="utf-8"
        )
        honeycomb = (ROOT / "protocol" / "HONEYCOMB_FIELD.md").read_text(encoding="utf-8")

        combined = "\n".join([agents, d1_doc, honeycomb])
        self.assertIn("Pure polygon overlap is permitted only inside the D1 geometry kernel", agents)
        self.assertIn("Pure polygon overlap is allowed only inside the D1 geometry kernel", honeycomb)
        self.assertIn("D1 is not recall. D1 is not placement.", d1_doc)
        self.assertIn("geometry recall", combined)
        self.assertIn("automatic card placement", combined)
        self.assertIn("parent-child ownership", combined)


def _distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return hypot(a[0] - b[0], a[1] - b[1])


def _vertex_angle_deg(point: tuple[float, float]) -> float:
    angle = degrees(atan2(point[1], point[0]))
    return angle + 360.0 if angle < 0 else angle


def _almost_equal(a: float, b: float, tolerance: float = 1e-9) -> bool:
    return abs(a - b) <= tolerance


def _coverage_for_target(rows, target: HexAddress):
    for row in rows:
        if row.target == target:
            return row
    raise AssertionError(f"missing target: {target}")


if __name__ == "__main__":
    unittest.main()
