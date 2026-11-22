"""Residual masks agree with independent integer rounding, including ties."""
from collections import Counter
from random import Random
import unittest
from unittest.mock import patch

from nollm_core import (
    GeometryAddress, UnsupportedPhysicalCoverage, clear_physical_coverage_cache,
    coverage_stencil_q40, expand_physical_coverage,
)
from nollm_core import approximate_coverage as kernel


S = 1 << 40


def cell(layer=0, q=0, r=0):
    return GeometryAddress("default_dream_v1", "default", layer, q, r)


def nearest_reference(q, r):
    """Independent ratio rounding and cube repair, without mask/rounder calls."""
    cube = (q, r, -q-r)
    rounded = []
    for value in cube:
        whole, remainder = divmod(value, S)
        rounded.append(whole + int(2*remainder > S or
                                  (2*remainder == S and whole % 2 != 0)))
    errors = [abs(rounded[i]*S-cube[i]) for i in range(3)]
    largest = errors.index(max(errors))
    rounded[largest] = -sum(rounded[i] for i in range(3) if i != largest)
    return rounded[0], rounded[1]


def full_reference(offsets, q, r):
    hits = Counter(nearest_reference(q+oq, r+or_) for oq, or_ in offsets)
    return tuple((tq, tr, n) for (tq, tr), n in sorted(hits.items()))


def weights_reference(counts):
    total = sum(counts)
    values = [n*65536//total for n in counts]
    order = sorted(range(len(counts)), key=lambda i: (-(counts[i]*65536 % total), i))
    for i in order[:65536-sum(values)]:
        values[i] += 1
    return tuple(values)


class ResidualMaskCoverageTests(unittest.TestCase):
    def setUp(self):
        clear_physical_coverage_cache()
        self.addCleanup(clear_physical_coverage_cache)

    def test_projected_bounds_cover_at_most_nine_targets_at_every_phase(self):
        for direction in ("coverage_up", "coverage_down"):
            _projected, (qlo, qhi, rlo, rhi) = kernel._projected_sample_masks(direction)
            # Width (offset_range/S + 4/3) < 3 is exact and phase independent.
            self.assertLess(3*(qhi-qlo)+4*S, 9*S)
            self.assertLess(3*(rhi-rlo)+4*S, 9*S)

    def test_phase_population_and_constructed_boundaries_match_integer_reference(self):
        rng = Random(20261122)
        for direction in ("coverage_up", "coverage_down"):
            offsets = coverage_stencil_q40(cell(), direction).offsets_q40
            phases = [(rng.randrange(2*S), rng.randrange(2*S)) for _ in range(1024)]
            phases.extend((q, r) for q in (0, 1, S//2, S, 3*S//2, 2*S-1)
                          for r in (0, 1, S//2, S, 3*S//2, 2*S-1))
            # Put each labelled point on each family of hex-face lines, then
            # sample both sides at one Q40 unit. Reduction is by even cells.
            for oq, or_ in offsets:
                boundary_points = ((0, (S-2*oq-or_) % (2*S)),
                                   ((S-oq-2*or_) % (2*S), 0),
                                   (0, (S+oq-or_) % (2*S)))
                for q, r in boundary_points:
                    phases.extend(((q+dq) % (2*S), (r+dr) % (2*S))
                                  for dq, dr in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)))
            for q, r in phases:
                actual = kernel._phase_footprint(direction, q, r)
                self.assertEqual(actual, full_reference(offsets, q, r), (direction, q, r))
                self.assertEqual(sum(n for _, _, n in actual), 96)

    def test_full_expansions_match_all_layers_and_signed_large_addresses(self):
        requests = [(layer, ((layer*7919) % 2000000001)-1000000000,
                     -(((layer*7919) % 2000000001)-1000000000)//2)
                    for layer in range(-64, 65)]
        requests.extend((0, q, r) for q, r in (
            (0, 0), (19, -17), (10**9, 0), (-10**9, 10**9),
            (2147483647, 0), (-2147483647, 0),
            (2147483647, -2147483647), (-2147483647, 2147483647)))
        for layer, q, r in requests:
            source = cell(layer, q, r)
            for direction in ("coverage_up", "coverage_down"):
                if (layer, direction) in ((-64, "coverage_up"), (64, "coverage_down")):
                    with self.assertRaises(UnsupportedPhysicalCoverage):
                        expand_physical_coverage(source, direction)
                    continue
                stencil = coverage_stencil_q40(source, direction)
                expected = full_reference(stencil.offsets_q40, *stencil.center_q40)
                outside = any(max(abs(a), abs(b), abs(a+b)) > 2147483647
                              for a, b, _ in expected)
                if outside:
                    with self.assertRaises(UnsupportedPhysicalCoverage):
                        expand_physical_coverage(source, direction)
                    continue
                result = expand_physical_coverage(source, direction)
                self.assertEqual(tuple((m.target.q, m.target.r, m.hit_count)
                                       for m in result.members), expected)
                self.assertEqual(tuple(m.weight_q16 for m in result.members),
                                 weights_reference([n for _, _, n in expected]))
                self.assertEqual(result.q16_sum, 65536)
                self.assertTrue(all(m.target.layer == layer+(-1 if direction == "coverage_up" else 1)
                                    for m in result.members))

    def test_coincident_samples_and_odd_half_even_ties_keep_original_rule(self):
        synthetic = (S//2, 0, S//2, 0, 0, 0, 0, 0)
        try:
            with patch.dict(kernel._TRANSFORMS, {"coverage_down": synthetic}):
                clear_physical_coverage_cache()
                nearest = kernel._nearest_axial_q40
                with patch.object(kernel, "_nearest_axial_q40", wraps=nearest) as calls:
                    first = expand_physical_coverage(cell(0, 1, 0), "coverage_down")
                    second = expand_physical_coverage(cell(0, 3, 0), "coverage_down")
                self.assertEqual(calls.call_count, 192)
                self.assertEqual([(m.target.q, m.target.r, m.hit_count) for m in first.members], [(1, 0, 96)])
                self.assertEqual([(m.target.q, m.target.r, m.hit_count) for m in second.members], [(1, 2, 96)])
                self.assertEqual(first.q16_sum, second.q16_sum)
        finally:
            clear_physical_coverage_cache()

    def test_interior_phase_counts_without_per_sample_rounding(self):
        for direction in ("coverage_up", "coverage_down"):
            source = cell(0, 19, -17)
            stencil = coverage_stencil_q40(source, direction)
            nearest = kernel._nearest_axial_q40
            with patch.object(kernel, "_nearest_axial_q40", wraps=nearest) as calls:
                result = expand_physical_coverage(source, direction)
            self.assertEqual(calls.call_count, 0)
            self.assertEqual(tuple((m.target.q, m.target.r, m.hit_count) for m in result.members),
                             full_reference(stencil.offsets_q40, *stencil.center_q40))

    def test_projection_cache_is_disposable_and_phase_cache_is_shared(self):
        before = [expand_physical_coverage(cell(layer, -7, 5), "coverage_down")
                  for layer in range(8)]
        phase_info = kernel._phase_footprint.cache_info()
        self.assertEqual((phase_info.misses, phase_info.hits), (1, 7))
        self.assertEqual(kernel._projected_sample_masks.cache_info().maxsize, 2)
        self.assertEqual(kernel._projected_sample_masks.cache_info().currsize, 1)
        clear_physical_coverage_cache()
        self.assertEqual(kernel._projected_sample_masks.cache_info().currsize, 0)
        self.assertEqual(kernel._phase_footprint.cache_info().currsize, 0)
        after = [expand_physical_coverage(cell(layer, -7, 5), "coverage_down")
                 for layer in range(8)]
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
