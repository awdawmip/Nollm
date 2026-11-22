"""Geometric uncertainty boundaries, rather than approximate equality checks."""
from fractions import Fraction as F
from itertools import product
from math import lcm
import unittest

from geometry.precision_budget import (
    certify_axial_ratio, minimum_safe_fraction_bits, quantize_axial_ratio,
)
from geometry.rational_coverage import nearest_axial_rational
from geometry.rational_affine_kernel import nearest_axial_ratio


def ratio(q, r):
    q, r = F(q), F(r)
    denominator = lcm(q.denominator, r.denominator)
    return (q.numerator * (denominator // q.denominator),
            r.numerator * (denominator // r.denominator), denominator)


class PrecisionBudgetTests(unittest.TestCase):
    def test_quantizer_signed_half_even_and_exact_large_integer_part(self):
        self.assertEqual(quantize_axial_ratio(1, 3, 2, 0), (0, 2, 1))
        self.assertEqual(quantize_axial_ratio(-1, -3, 2, 0), (0, -2, 1))
        self.assertEqual(quantize_axial_ratio(5, -7, 2, 0), (2, -4, 1))
        self.assertEqual(quantize_axial_ratio(3, -7, 8, 2), (2, -4, 4))
        point = ratio(2**160 + F(3, 8), -2**150 - F(7, 8))
        self.assertEqual(quantize_axial_ratio(*point, 2),
                         (2**162 + 2, -2**152 - 4, 4))

    def test_quantizer_respects_stated_error_against_fraction_round(self):
        for numerator, denominator, bits in product(range(-17, 18), (3, 7, 11), range(7)):
            q, r, scale = quantize_axial_ratio(numerator, -2*numerator, denominator, bits)
            for exact, rounded in ((F(numerator, denominator), q),
                                   (F(-2*numerator, denominator), r)):
                self.assertEqual(rounded, round(exact * scale))
                self.assertLessEqual(abs(F(rounded, scale) - exact), F(1, 2*scale))

    def test_certified_rectangles_keep_every_corner_in_the_same_cell(self):
        points = ((0, 0), (F(1, 4), F(1, 5)), (F(11, 20), F(-3, 10)),
                  (F(-5, 3), F(17, 11)), (2**80 + F(1, 10), -2**90 + F(2, 17)))
        certified = 0
        for (q, r), denominator in product(points, (16, 64, 1000)):
            eq, er = F(1, denominator), F(1, 2*denominator)
            cell = certify_axial_ratio(*ratio(q, r), eq, er)
            if cell is None:
                continue
            certified += 1
            for sq, sr in product((-1, 0, 1), repeat=2):
                self.assertEqual(nearest_axial_rational(q + sq*eq, r + sr*er), cell)
        self.assertGreater(certified, 5)

    def test_error_rectangle_crossing_a_face_is_inconclusive(self):
        point = ratio(F(1, 2) - F(1, 1000), 0)
        self.assertEqual(nearest_axial_ratio(*point), (0, 0))
        self.assertIsNone(certify_axial_ratio(*point, F(1, 1000)))
        self.assertEqual(nearest_axial_rational(F(1, 2), F(1, 1000)), (1, 0))
        self.assertEqual(certify_axial_ratio(*point, F(1, 10000)), (0, 0))

    def test_zero_error_respects_boundary_tie_but_positive_box_is_not_certified(self):
        for point in (ratio(F(1, 2), 0), ratio(F(-1, 2), 0), ratio(F(1, 3), F(1, 3))):
            self.assertEqual(certify_axial_ratio(*point), nearest_axial_ratio(*point))
            self.assertIsNone(certify_axial_ratio(*point, F(1, 2**100)))
            self.assertIsNone(minimum_safe_fraction_bits(*point))

    def test_nonmonotone_actual_rounding_and_monotone_certificate(self):
        point = ratio(F(1, 3), F(3, 10))
        exact = nearest_axial_ratio(*point)
        outcomes = [nearest_axial_ratio(*quantize_axial_ratio(*point, bits))
                    for bits in range(7)]
        self.assertEqual(outcomes, [(0, 0), (1, 0), (0, 0), (1, 0), (0, 0), (1, 0), (0, 0)])
        self.assertEqual(minimum_safe_fraction_bits(*point), 6)
        self.assertIsNone(certify_axial_ratio(*point, F(1, 2**6)))
        for bits in range(6, 14):
            self.assertEqual(certify_axial_ratio(*point, F(1, 2**(bits+1))), exact)
            self.assertEqual(nearest_axial_ratio(*quantize_axial_ratio(*point, bits)), exact)

    def test_arbitrarily_small_residual_can_require_more_than_q40(self):
        point = ratio(F(1, 2) + F(1, 2**60), 0)
        self.assertEqual(minimum_safe_fraction_bits(*point), 60)
        self.assertEqual(nearest_axial_ratio(*point), (1, 0))
        self.assertEqual(nearest_axial_ratio(*quantize_axial_ratio(*point, 59)), (0, 0))
        self.assertEqual(nearest_axial_ratio(*quantize_axial_ratio(*point, 60)), (1, 0))
        self.assertEqual(minimum_safe_fraction_bits(0, 0, 1), 1)

    def test_precision_and_error_preconditions_preserve_the_bound_meaning(self):
        with self.assertRaises(ValueError):
            quantize_axial_ratio(0, 0, 1, -1)
        with self.assertRaises(ValueError):
            minimum_safe_fraction_bits(0, 0, 0)
        with self.assertRaises(ValueError):
            certify_axial_ratio(0, 0, 1, -1)
        with self.assertRaises(TypeError):
            certify_axial_ratio(0, 0, 1, 0.001)


if __name__ == "__main__":
    unittest.main()
