"""Exact identities and input meaning for rational axial geometry."""
from dataclasses import replace
from fractions import Fraction
import json
import unittest

from geometry.rational_geometry import (
    Q, RATIONAL_MAP_CONTRACT_ID, RationalAffine, RationalLayerMap,
    RationalRadialTwist, axial_norm2, rational_from_mapping, rational_rotation,
    rational_to_mapping, relative_layer_maps,
)


def apply(matrix, point):
    return tuple(sum(row[i]*point[i] for i in range(2)) for row in matrix)


class RationalGeometryTests(unittest.TestCase):
    def test_input_value_and_json_components_keep_intended_rational(self):
        self.assertEqual(Q("0.1"), Fraction(1, 10))
        self.assertEqual(Q("-17/51"), Fraction(-1, 3))
        self.assertEqual(Q(2**160+1), 2**160+1)
        with self.assertRaisesRegex(TypeError, "float"):
            Q(0.1)
        with self.assertRaisesRegex(TypeError, "float"):
            RationalAffine(origin=(0.1, 0))
        value = Fraction(-(2**180+1), 2**91+3)
        stored = json.loads(json.dumps(rational_to_mapping(value)))
        self.assertIsInstance(stored["numerator"], str)
        self.assertIsInstance(stored["denominator"], str)
        self.assertEqual(rational_from_mapping(stored), value)
        with self.assertRaisesRegex(TypeError, "strings"):
            rational_from_mapping({"numerator": 0.5, "denominator": 1})

    def test_rotation_preserves_axial_metric_and_has_exact_inverse(self):
        points = ((0, 0), (1, 0), (0, 1), (2, -3),
                  (Fraction(7, 13), Fraction(-11, 17)))
        for t in (Fraction(0), Fraction(1, 9), Fraction(-4, 7), Fraction(17, 3)):
            rotation = rational_rotation(t)
            (a, b), (c, d) = rotation
            self.assertEqual(a*d-b*c, 1)
            # Independent matrix identity C^T G C = G, with 2G integral.
            for i in range(2):
                for j in range(2):
                    actual = sum(rotation[k][i]*((2, 1), (1, 2))[k][m]*rotation[m][j]
                                 for k in range(2) for m in range(2))
                    self.assertEqual(actual, ((2, 1), (1, 2))[i][j])
            for point in points:
                moved = apply(rotation, point)
                self.assertEqual(axial_norm2(moved), axial_norm2(point))
                self.assertEqual(apply(rational_rotation(-t), moved), point)
        self.assertEqual(rational_rotation(1), ((Fraction(-1), Fraction(-1)),
                                                (Fraction(1), Fraction(0))))
        self.assertEqual(rational_rotation("1/3"), ((Fraction(0), Fraction(-1)),
                                                    (Fraction(1), Fraction(1))))

    def test_affine_inverse_composition_and_reanchor_are_exact(self):
        first = RationalAffine((("7/5", "-2/3"), ("1/4", "9/8")),
                               (2**100+1, "-5/7"), ("2/3", "-7/9"))
        second = RationalAffine.similarity("3/2", "1/11", origin=("-2/5", "7/4"),
                                            local_anchor=("1/3", "2/7"))
        composed = first.after(second)
        reanchored = first.reanchor((2**80+1, Fraction(-7, 19)))
        for point in ((0, 0), (1, -2), (Fraction(3, 17), Fraction(-9, 23)), (2**120+1, -2**130)):
            self.assertEqual(first.inverse(first.forward(point)), point)
            self.assertEqual(first.forward(first.inverse(point)), point)
            self.assertEqual(first.inverse_frame().forward(point), first.inverse(point))
            self.assertEqual(first.inverse_frame().inverse(point), first.forward(point))
            self.assertEqual(composed.forward(point), first.forward(second.forward(point)))
            self.assertEqual(composed.inverse(composed.forward(point)), point)
            self.assertEqual(reanchored.forward(point), first.forward(point))
        self.assertEqual(second.determinant, Fraction(9, 4))
        self.assertEqual(first.determinant, composed.determinant/second.determinant)

    def test_one_unit_survives_huge_world_anchor(self):
        origin = 2**160
        frame = RationalAffine(origin=(origin+1, -origin), local_anchor=(0, 0))
        target = RationalAffine(origin=(origin, -origin))
        self.assertEqual(target.inverse(frame.forward((0, 0))), (1, 0))
        self.assertEqual(target.inverse(frame.forward((Fraction(1, 17), Fraction(3, 19)))),
                         (Fraction(18, 17), Fraction(3, 19)))

    def test_twist_preserves_radius_with_analytic_inverse_and_compact_boundary(self):
        center = (Fraction(2, 7), Fraction(-5, 11))
        twist = RationalRadialTwist(center, 1, "-5/3")
        deltas = ((0, 0), (Fraction(1, 3), Fraction(1, 7)),
                  (Fraction(7, 8), 0), (1, 0), (0, -1), (2, -1))
        for delta in deltas:
            point = tuple(c+d for c, d in zip(center, delta))
            moved = twist.forward(point)
            shifted = tuple(p-c for p, c in zip(moved, center))
            self.assertEqual(axial_norm2(shifted), axial_norm2(delta))
            self.assertEqual(twist.inverse(moved), point)
            self.assertEqual(twist.forward(twist.inverse(point)), point)
            if axial_norm2(delta) >= 1:
                self.assertEqual(moved, point)
        self.assertEqual(twist.forward(center), center)
        inside = (center[0]+Fraction(1, 3), center[1])
        self.assertNotEqual(twist.forward(inside), inside)
        self.assertEqual(replace(twist, strength=0).forward(inside), inside)
        self.assertNotEqual(twist.with_center((3, 5)).forward(inside), twist.forward(inside))

    def test_multiple_twists_reverse_order_and_local_reanchor(self):
        mapping = RationalLayerMap(RationalAffine.similarity("2/3", "-1/7", origin=("1/8", "2/9")),
                                   (RationalRadialTwist((0, 0), 3, "1/9"),
                                    RationalRadialTwist(("1/7", "-1/9"), 2, "-2/11")))
        reanchored = mapping.reanchor((2**75+1, Fraction(-5, 17)))
        for point in ((0, 0), (Fraction(1, 3), Fraction(-1, 4)), (2, -1)):
            mapped = mapping.forward(point)
            self.assertEqual(mapping.inverse(mapped), point)
            self.assertEqual(mapping.forward(mapping.inverse(point)), point)
            self.assertEqual(reanchored.forward(point), mapped)

    def test_common_world_rebase_moves_origins_and_all_centers(self):
        anchor = (2**180, -2**170)
        source = RationalLayerMap(
            RationalAffine.similarity("3/4", "1/13", origin=(anchor[0]+1, anchor[1]-2),
                                       local_anchor=("1/11", "-2/17")),
            (RationalRadialTwist((anchor[0]+1, anchor[1]), 4, "1/3"),))
        target = RationalLayerMap(
            RationalAffine(origin=anchor),
            (RationalRadialTwist((anchor[0], anchor[1]+1), 3, "-1/5"),
             RationalRadialTwist((anchor[0]-2, anchor[1]), 5, "1/7")))
        old = source.to_mapping(), target.to_mapping()
        rebased_source, rebased_target = relative_layer_maps(source, target)
        self.assertEqual(rebased_source.frame.origin, (1, -2))
        self.assertEqual(rebased_target.frame.origin, (0, 0))
        self.assertEqual(rebased_source.frame.local_anchor, source.frame.local_anchor)
        self.assertEqual(rebased_source.twists[0].center, (1, 0))
        self.assertEqual(tuple(t.center for t in rebased_target.twists), ((0, 1), (-2, 0)))
        for point in ((0, 0), (Fraction(1, 4), Fraction(-2, 7)), (3, -1)):
            expected = target.inverse(source.forward(point))
            actual = rebased_target.inverse(rebased_source.forward(point))
            self.assertEqual(actual, expected)
        self.assertEqual((source.to_mapping(), target.to_mapping()), old)

    def test_complete_map_json_roundtrip_preserves_exact_values_and_behavior(self):
        mapping = RationalLayerMap(
            RationalAffine.similarity("17/19", "-3/31", origin=(2**160+1, "2/7"),
                                       local_anchor=("-3/11", "5/13")),
            (RationalRadialTwist((2**160+1, "2/7"), "5/17", "2/23"),))
        serialized = json.loads(json.dumps(mapping.to_mapping()))
        self.assertEqual(serialized["contract_id"], RATIONAL_MAP_CONTRACT_ID)
        restored = RationalLayerMap.from_mapping(serialized)
        self.assertEqual(restored, mapping)
        point = (Fraction(2, 29), Fraction(-3, 31))
        self.assertEqual(restored.forward(point), mapping.forward(point))
        self.assertEqual(restored.inverse(restored.forward(point)), point)
        with self.assertRaisesRegex(ValueError, "contract"):
            RationalLayerMap.from_mapping({**serialized, "contract_id": "float64"})

    def test_map_domain_errors_are_mathematical_preconditions(self):
        with self.assertRaisesRegex(ValueError, "invertible"):
            RationalAffine(((1, 2), (2, 4)))
        with self.assertRaisesRegex(ValueError, "positive"):
            RationalAffine.similarity(0, 0)
        with self.assertRaisesRegex(ValueError, "positive"):
            RationalRadialTwist(radius_squared=0)
        with self.assertRaisesRegex(TypeError, "float"):
            rational_rotation(0.25)


if __name__ == "__main__":
    unittest.main()
