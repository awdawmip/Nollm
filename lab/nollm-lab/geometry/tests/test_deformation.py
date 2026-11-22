"""Explicit map invariants and independent finite coverage comparisons."""
from collections import Counter
from decimal import Decimal, localcontext
import json
from math import cos, sin
from pathlib import Path
import random
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from deformation import (
    DEFORMATION_CONTRACT_ID, Q40_ONE, LayerMap, RadialTwist,
    SimilarityFrame, sampled_coverage,
)
from physical_geometry import PI, beta, sin_cos
from nollm_core import (
    GeometryAddress, coverage_sample_offsets_q40, nearest_axial_q40,
    normalize_q16_weights,
)


def cell(layer=0, q=0, r=0):
    return GeometryAddress("default_dream_v1", "default", layer, q, r)


def records(result):
    return tuple((m.target.q, m.target.r, m.hit_count, m.weight_q16) for m in result.members)


def decimal_default_reference(source, target_layer):
    """Independent 72-digit chart calculation, using the fixed source samples."""
    with localcontext() as ctx:
        ctx.prec = 72
        root3 = Decimal(3).sqrt()
        scale = beta() ** Decimal(target_layer-source.layer)
        sine, cosine = sin_cos(Decimal(source.layer-target_layer)*PI/8)
        cx = root3 * (Decimal(source.q) + Decimal(source.r)/2)
        cy = Decimal(3)*source.r/2
        targets = []
        for ox, oy in coverage_sample_offsets_q40():
            x, y = cx+Decimal(ox)/Q40_ONE, cy+Decimal(oy)/Q40_ONE
            tx, ty = scale*(cosine*x-sine*y), scale*(sine*x+cosine*y)
            q, r = tx/root3-ty/3, 2*ty/3
            targets.append(nearest_axial_q40(round(q*Q40_ONE), round(r*Q40_ONE)))
        counts = sorted(Counter(targets).items())
        weights = normalize_q16_weights([n for _, n in counts])
        return tuple((q, r, n, w) for ((q, r), n), w in zip(counts, weights))


class DeformationTests(unittest.TestCase):
    def assertPointClose(self, actual, expected, places=10):
        self.assertAlmostEqual(actual[0], expected[0], places=places)
        self.assertAlmostEqual(actual[1], expected[1], places=places)

    def test_similarity_inverse_reanchor_and_composition(self):
        frame = SimilarityFrame((3, -7), (0.2, 0.4), 1.8, 0.37)
        reframed = frame.reanchor((-11, 4))
        outer = SimilarityFrame((-0.2, 8), (1, 1), 0.7, -0.43)
        for point in ((0, 0), (3, -1), (-2, 1), (100, -70)):
            self.assertPointClose(frame.inverse(frame.forward(point)), point)
            self.assertPointClose(reframed.forward(point), frame.forward(point))
            self.assertPointClose(outer.after(frame).forward(point), outer.forward(frame.forward(point)))

    def test_actual_pivot_change_changes_map(self):
        frame = SimilarityFrame((3, 1), scale=1.2, angle=0.4)
        point = (2, -1)
        center, angle = (-1, 3), 0.8
        x, y = frame.forward(point)
        x, y = x-center[0], y-center[1]
        expected = center[0]+cos(angle)*x-sin(angle)*y, center[1]+sin(angle)*x+cos(angle)*y
        self.assertPointClose(frame.rotate_about(center, angle).forward(point), expected)
        self.assertNotEqual(frame.rotate_about((0, 0), angle).forward(point), expected)

    def test_twist_inverse_radius_and_compact_support(self):
        rng = random.Random(812)
        twist = RadialTwist((0.3, -0.7), 4, 3.2)
        for point in [(0.3, -0.7), (4.3, -0.7), (6, 8),
                      *((rng.uniform(-5, 5), rng.uniform(-5, 5)) for _ in range(150))]:
            mapped = twist.forward(point)
            self.assertPointClose(twist.inverse(mapped), point)
            radius2 = lambda p: (p[0]-twist.center[0])**2+(p[1]-twist.center[1])**2
            self.assertAlmostEqual(radius2(mapped), radius2(point), places=10)
            if radius2(point) >= twist.radius**2:
                self.assertEqual(mapped, point)
        self.assertNotEqual(twist.forward((1, 1)), twist.with_center((1, -1)).forward((1, 1)))

    def test_twist_local_jacobian_matches_analytic_unit_determinant(self):
        twist = RadialTwist((0.2, -0.4), 3, 1.7)
        h = 1e-6
        for x, y in ((0.2, -0.4), (0.9, 0.4), (-0.7, 1.4), (3.2, -0.4), (5, 4)):
            a, b = twist.forward((x+h, y)), twist.forward((x-h, y))
            c, d = twist.forward((x, y+h)), twist.forward((x, y-h))
            dx = (a[0]-b[0])/(2*h), (a[1]-b[1])/(2*h)
            dy = (c[0]-d[0])/(2*h), (c[1]-d[1])/(2*h)
            determinant = dx[0]*dy[1]-dx[1]*dy[0]
            self.assertAlmostEqual(determinant, 1.0, delta=2e-5)

    def test_layer_map_round_trip_and_json_recovery(self):
        mapping = LayerMap(
            SimilarityFrame((1, 2), (0.4, -0.3), 1.1, 0.2),
            (RadialTwist((2, -1), 10, 0.7), RadialTwist((-1, 1), 8, -0.2)),
        )
        recovered = LayerMap.from_mapping(json.loads(json.dumps(mapping.to_mapping())))
        self.assertEqual(recovered, mapping)
        for point in ((0, 0), (0.3, 1.1), (-4, 3), (10, -10)):
            self.assertPointClose(recovered.inverse(recovered.forward(point)), point)
            self.assertPointClose(mapping.reanchor((1, 7)).forward(point), mapping.forward(point))

    def test_default_sample_counts_agree_with_independent_decimal_fixture(self):
        for source in (cell(0, 3, -5), cell(-2, 7, 2), cell(5, -11, 9)):
            for target_layer in (source.layer-1, source.layer+1):
                result = sampled_coverage(source, target_layer)
                self.assertEqual(records(result), decimal_default_reference(source, target_layer))
                self.assertEqual(result.contract_id, DEFORMATION_CONTRACT_ID)
                self.assertEqual(sum(m.hit_count for m in result.members), 96)
                self.assertEqual(sum(m.weight_q16 for m in result.members), 65536)

    def test_common_similarity_and_common_twist_preserve_coverage_on_nontie_fixture(self):
        source = cell(0, 3, -5)
        origin = LayerMap.for_layer(0)
        target = LayerMap.for_layer(1)
        baseline = records(sampled_coverage(source, 1, origin, target))
        common = SimilarityFrame((3, -2), (0.1, -0.3), 1.4, 0.63)
        self.assertEqual(records(sampled_coverage(source, 1,
                         LayerMap(common.after(origin.frame)),
                         LayerMap(common.after(target.frame)))), baseline)
        twist = RadialTwist((1, -2), 20, 1.2)
        self.assertEqual(records(sampled_coverage(source, 1,
                         origin.with_twist(twist), target.with_twist(twist))), baseline)
        self.assertEqual(records(sampled_coverage(source, 1,
                         origin.reanchor((8, 3)), target.reanchor((-2, 4)))), baseline)

    def test_relative_translation_and_twist_change_coverage(self):
        source = cell(0, 1, 0)
        origin, target = LayerMap.for_layer(0), LayerMap.for_layer(1)
        baseline = records(sampled_coverage(source, 1, origin, target))
        shifted = LayerMap(SimilarityFrame((0.6, -0.2), scale=target.frame.scale,
                                          angle=target.frame.angle))
        twisted = target.with_twist(RadialTwist((0.3, 0.2), 5, 1.0))
        self.assertNotEqual(records(sampled_coverage(source, 1, origin, shifted)), baseline)
        self.assertNotEqual(records(sampled_coverage(source, 1, origin, twisted)), baseline)
        recovered = LayerMap.from_mapping(json.loads(json.dumps(twisted.to_mapping())))
        self.assertEqual(sampled_coverage(source, 1, origin, recovered),
                         sampled_coverage(source, 1, origin, twisted))

    def test_math_domain_errors_are_explicit(self):
        with self.assertRaises(ValueError):
            SimilarityFrame(scale=0)
        with self.assertRaises(ValueError):
            RadialTwist(radius=-1)
        with self.assertRaises(ValueError):
            sampled_coverage(cell(), 2)
        with self.assertRaises(ValueError):
            LayerMap.from_mapping({"contract_id": "unrecognized"})

    def test_read_only_cli_outputs_recoverable_maps_and_coverage(self):
        script = Path(__file__).resolve().parents[1] / "deformation_cli.py"
        result = subprocess.run([sys.executable, str(script), "coverage", "--source", "0", "1", "0",
                                 "--target-layer", "1", "--twist", "0.3", "0.2", "5", "1"],
                                check=True, capture_output=True, text=True)
        output = json.loads(result.stdout)
        source_map = LayerMap.from_mapping(output["source_map"])
        target_map = LayerMap.from_mapping(output["target_map"])
        self.assertEqual(output["coverage"], sampled_coverage(cell(0, 1, 0), 1,
                                                            source_map, target_map).to_mapping())
        result = subprocess.run([sys.executable, str(script), "motion", "--delta-q40", "1", "-1"],
                                check=True, capture_output=True, text=True)
        output = json.loads(result.stdout)
        self.assertTrue(output["matches_full"])
        self.assertEqual(output["round_calls"], 0)


if __name__ == "__main__":
    unittest.main()
