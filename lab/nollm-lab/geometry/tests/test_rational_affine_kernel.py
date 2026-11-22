from fractions import Fraction as F
import random
import unittest

from geometry.rational_affine_kernel import (
    CompiledRationalAffine, compile_affine_pair, nearest_axial_ratio,
)
from geometry.rational_geometry import RationalAffine, RationalLayerMap, RationalRadialTwist


def reference_round(q, r):
    x, z, y = round(q), round(r), round(-q-r)
    dx, dz, dy = abs(F(x)-q), abs(F(z)-r), abs(F(y)+q+r)
    if dx >= dz and dx >= dy:
        x = -y-z
    elif dz >= dy:
        z = -x-y
    return x, z


class RationalAffineKernelTests(unittest.TestCase):
    def test_exact_ratio_classification_including_ties_and_signed_large_values(self):
        for divisor in (1, 2, 3, 7, 36, 2**42, 10**35+1):
            for q in (-3*divisor, -divisor//2, -1, 0, 1, divisor//2, 3*divisor):
                for r in (-divisor, -1, 0, 1, divisor):
                    self.assertEqual(nearest_axial_ratio(q, r, divisor),
                                     reference_round(F(q, divisor), F(r, divisor)))
        self.assertEqual(nearest_axial_ratio(2**41+1, 0, 2**42), (1, 0))

    def test_compiled_coefficients_preserve_full_rational_coordinates(self):
        rng = random.Random(20261122)
        for _ in range(20):
            frame = RationalAffine.similarity(F(rng.randrange(1, 8), 5),
                    F(rng.randrange(-3, 4), 7),
                    origin=(F(rng.randrange(-100, 101), 11), F(7, 13)),
                    local_anchor=(F(1, 3), F(-5, 17)))
            kernel = CompiledRationalAffine.from_frame(frame)
            for _ in range(12):
                q, r, denominator = rng.randrange(-100, 101), rng.randrange(-100, 101), 36
                nq, nr, nd = kernel.map_ratio(q, r, denominator)
                self.assertEqual((F(nq, nd), F(nr, nd)), frame.forward((F(q, 36), F(r, 36))))

    def test_large_common_anchor_and_one_unit_difference_remain_exact(self):
        anchor = 2**200
        source = RationalLayerMap(RationalAffine(origin=(anchor+1, anchor)))
        target = RationalLayerMap(RationalAffine(origin=(anchor, anchor)))
        kernel = compile_affine_pair(source, target)
        self.assertEqual(kernel.map_ratio(1, 2, 3), (4, 2, 3))
        self.assertEqual(kernel.targets(0, 0, ((0, 0),), 36), ((1, 0),))

    def test_common_nonlinear_world_maps_cancel_exactly(self):
        twists = (RationalRadialTwist((0, 0), 1, F(1, 5)),
                  RationalRadialTwist((F(1, 5), 0), 1, F(-1, 7)))
        source = RationalLayerMap(RationalAffine.similarity(F(4, 5), F(1, 7)), twists)
        target = RationalLayerMap(RationalAffine.similarity(F(6, 5), F(-1, 9)), twists)
        kernel = compile_affine_pair(source, target)
        for q, r in ((1, 2), (-2, 1), (3, -1), (0, 0)):
            exact = target.inverse(source.forward((F(q, 36), F(r, 36))))
            nq, nr, nd = kernel.map_ratio(q, r, 36)
            self.assertEqual((F(nq, nd), F(nr, nd)), exact)

    def test_distinct_twists_do_not_compile_as_affine(self):
        base = RationalLayerMap()
        twist = RationalRadialTwist(strength=F(1, 5))
        self.assertIsNone(compile_affine_pair(base.with_twist(twist), base))
        self.assertIsNone(compile_affine_pair(base.with_twist(twist),
            base.with_twist(twist.with_center((1, 0)))))

    def test_compiled_stencil_matches_direct_evaluation(self):
        source = RationalLayerMap(RationalAffine(((F(4, 5), F(1, 9)), (F(-1, 7), F(5, 4))),
                                               origin=(F(2, 3), F(-4, 5))))
        target = RationalLayerMap(RationalAffine.similarity(F(6, 5), F(1, 8),
                                               local_anchor=(F(1, 7), F(2, 9))))
        offsets = tuple((i, j) for i in range(-8, 9, 2) for j in range(-7, 8, 2))
        kernel = compile_affine_pair(source, target)
        for q, r in ((-9, 5), (0, 0), (2**100, -2**100+1)):
            expected = tuple(reference_round(*target.inverse(source.forward(
                (q+F(dq, 36), r+F(dr, 36))))) for dq, dr in offsets)
            self.assertEqual(kernel.targets(q, r, offsets, 36), expected)


if __name__ == "__main__":
    unittest.main()
