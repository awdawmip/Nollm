"""Inverse completeness is compared with a wider forward search, not down hits."""
from fractions import Fraction
from math import floor
import random
import unittest

from nollm_core import (
    GeometryAddress,
    UnsupportedPhysicalCoverage,
    clear_physical_coverage_cache,
    expand_physical_coverage,
    incoming_coverage,
    incoming_coverage_candidates,
)
from nollm_core.approximate_coverage import _TRANSFORMS, _compiled_sample_offsets_q40


S = 1 << 40
RADIUS = (1 << 31) - 1


def cell(layer, q=0, r=0):
    return GeometryAddress("default_dream_v1", "default", layer, q, r)


def wider_forward_search(parent):
    """Independent Fraction inverse center and a 9x9 direct forward window."""
    a, b, c, d = _TRANSFORMS["coverage_up"][:4]
    determinant = a * d - b * c
    q0 = floor(Fraction(S * (d * parent.q - b * parent.r), determinant))
    r0 = floor(Fraction(S * (-c * parent.q + a * parent.r), determinant))
    found = {}
    for q in range(q0 - 4, q0 + 5):
        for r in range(r0 - 4, r0 + 5):
            if max(abs(q), abs(r), abs(q + r)) > RADIUS:
                continue
            source = cell(parent.layer + 1, q, r)
            for member in expand_physical_coverage(source, "coverage_up").members:
                if member.target == parent:
                    found[source] = member.weight_q16, member.hit_count
    return found


class IncomingCoverageTests(unittest.TestCase):
    def test_known_nonreciprocal_witness_is_included(self):
        parent = cell(0, 67, 5)
        omitted = cell(1, 94, -30)
        down = {m.target for m in expand_physical_coverage(parent, "coverage_down").members}
        self.assertNotIn(omitted, down)
        result = incoming_coverage(parent)
        found = {m.source: (m.weight_q16, m.hit_count) for m in result.members}
        self.assertEqual(found[omitted], (683, 1))
        self.assertEqual(len(found), 6)
        self.assertEqual(result.candidate_count, 9)
        self.assertTrue(result.complete)

    def test_complete_against_wider_forward_window(self):
        rng = random.Random(20261122)
        positions = [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (67, 5),
                     (10**9, -10**9), (-10**9, 10**9), (RADIUS, 0),
                     (0, -RADIUS), (RADIUS, -RADIUS)]
        positions.extend((rng.randrange(-10**7, 10**7), rng.randrange(-10**7, 10**7))
                         for _ in range(32))
        for index, (q, r) in enumerate(positions):
            parent = cell((-64, -7, -1, 0, 6, 63)[index % 6], q, r)
            with self.subTest(parent=parent):
                result = incoming_coverage(parent)
                self.assertEqual(
                    {m.source: (m.weight_q16, m.hit_count) for m in result.members},
                    wider_forward_search(parent),
                )
                self.assertLessEqual(result.candidate_count, 9)
                self.assertTrue(result.complete)

    def test_template_width_bound_is_global_not_a_sampled_maximum(self):
        a, b, c, d = _TRANSFORMS["coverage_up"][:4]
        determinant = a * d - b * c
        vertices = [(Fraction(q, 3), Fraction(r, 3))
                    for q, r in ((1, 1), (-1, 2), (-2, 1), (-1, -1), (1, -2), (2, -1))]
        offsets = _compiled_sample_offsets_q40("coverage_up")
        for row in ((Fraction(d, determinant), Fraction(-b, determinant)),
                    (Fraction(-c, determinant), Fraction(a, determinant))):
            h = [S * (row[0] * q + row[1] * r) for q, r in vertices]
            o = [row[0] * q + row[1] * r for q, r in offsets]
            width = max(h) - min(h) + max(o) - min(o)
            self.assertGreater(width, 2)
            self.assertLess(width, 3)

    def test_member_weights_preserve_each_sources_complete_normalization(self):
        source = cell(1, -7, 5)
        direct = expand_physical_coverage(source, "coverage_up")
        recovered = []
        for member in direct.members:
            incoming = incoming_coverage(member.target)
            recovered.append(next(m.weight_q16 for m in incoming.members if m.source == source))
        self.assertEqual(recovered, [m.weight_q16 for m in direct.members])
        self.assertEqual(sum(recovered), 1 << 16)

    def test_layer_and_storage_boundaries(self):
        with self.assertRaises(UnsupportedPhysicalCoverage):
            incoming_coverage_candidates(cell(64))
        self.assertTrue(incoming_coverage(cell(-64)).complete)
        for q, r in ((RADIUS, 0), (0, RADIUS), (-RADIUS, 0),
                     (0, -RADIUS), (RADIUS, -RADIUS), (-RADIUS, RADIUS)):
            for candidate in incoming_coverage_candidates(cell(0, q, r)):
                self.assertLessEqual(max(abs(candidate.q), abs(candidate.r),
                                         abs(candidate.q + candidate.r)), RADIUS)

    def test_order_and_disposable_forward_cache(self):
        parent = cell(-3, -81, 12)
        before = incoming_coverage(parent)
        clear_physical_coverage_cache()
        self.assertEqual(incoming_coverage(parent), before)
        keys = [m.source.stable_key() for m in before.members]
        self.assertEqual(keys, sorted(keys))


if __name__ == "__main__":
    unittest.main()
