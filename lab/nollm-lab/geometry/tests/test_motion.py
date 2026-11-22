"""Translation reuse against independent full absolute-coordinate evaluation."""
from collections import Counter
from fractions import Fraction
from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from motion import Q40_ONE as S, NORMALS, TranslationFootprint
from nollm_core import (
    GeometryAddress, coverage_stencil_q40, nearest_axial_q40,
    expand_physical_coverage, normalize_q16_weights,
)


def cell(q=0, r=0):
    return GeometryAddress("default_dream_v1", "default", 0, q, r)


def full_reference(direction, center):
    offsets = coverage_stencil_q40(cell(), direction).offsets_q40
    targets = tuple(nearest_axial_q40(center[0] + dq, center[1] + dr)
                    for dq, dr in offsets)
    counts = sorted(Counter(targets).items())
    weights = normalize_q16_weights([n for _, n in counts])
    records = tuple((q, r, n, w) for ((q, r), n), w in zip(counts, weights))
    return targets, records


class MotionTests(unittest.TestCase):
    def assertMatchesFull(self, footprint):
        targets, counts = full_reference(footprint.direction, footprint.center_q40)
        self.assertEqual(footprint.sample_targets(), targets)
        self.assertEqual(footprint.counts_q16(), counts)
        self.assertEqual(sum(row[2] for row in counts), 96)
        self.assertEqual(sum(row[3] for row in counts), 65536)

    def test_initial_footprints_match_current_public_kernel(self):
        for direction in ("coverage_up", "coverage_down"):
            for q, r in ((0, 0), (19, -17), (10**9, -10**9), (-10**9, 0)):
                source = cell(q, r)
                footprint = TranslationFootprint.from_source(source, direction)
                production = expand_physical_coverage(source, direction)
                expected = tuple((m.target.q, m.target.r, m.hit_count, m.weight_q16)
                                 for m in production.members)
                self.assertEqual(footprint.counts_q16(), expected)
                self.assertMatchesFull(footprint)

    def test_small_safe_step_reuses_certificate_arrays(self):
        footprint = TranslationFootprint.from_source(cell(19, -17), "coverage_up")
        step = footprint.translate((1, -1))
        self.assertEqual(step.mode, "reuse")
        self.assertEqual(step.round_calls, 0)
        self.assertIs(step.footprint._points, footprint._points)
        self.assertIs(step.footprint._margins, footprint._margins)
        self.assertMatchesFull(step.footprint)

    def test_even_translation_reuses_tie_footprint_and_odd_translation_does_not_assume_it(self):
        offset = coverage_stencil_q40(cell(), "coverage_down").offsets_q40[0]
        original = TranslationFootprint.from_center_q40(
            "coverage_down", (S // 2 - offset[0], -offset[1]))
        even = original.translate((2 * S, -4 * S))
        self.assertEqual(even.round_calls, 0)
        self.assertEqual(even.changed_samples, 96)
        self.assertMatchesFull(even.footprint)
        odd = original.translate((S, 0))
        self.assertEqual(odd.mode, "full")
        self.assertEqual(odd.round_calls, 96)
        self.assertMatchesFull(odd.footprint)

    def test_boundary_and_odd_anchor_cases_match_full(self):
        for direction in ("coverage_up", "coverage_down"):
            ox, oy = coverage_stencil_q40(cell(), direction).offsets_q40[0]
            for q2, r2 in ((1, 0), (3, 0), (-1, 0), (-3, 0), (0, 1), (0, 3)):
                base = TranslationFootprint.from_center_q40(
                    direction, (q2 * S // 2 - ox, r2 * S // 2 - oy))
                for shift in ((0, 0), (1, -1), (-1, 1), (S, 0), (-S, 0),
                              (2*S, 0), (S//100, -S//100)):
                    self.assertMatchesFull(base.translate(shift).footprint)

    def test_random_sequence_updates_cache_and_matches_direct_reference(self):
        rng = random.Random(20261122)
        for direction in ("coverage_up", "coverage_down"):
            for q, r in ((0, 0), (17, -23), (10**9, -10**9), (-10**9, 0)):
                state = TranslationFootprint.from_source(cell(q, r), direction)
                center = state.center_q40
                for i in range(160):
                    scale = (1, S//10**4, S//100, S, 4*S)[i % 5]
                    delta = rng.randrange(-scale, scale+1), rng.randrange(-scale, scale+1)
                    expected_step = state.translate(delta, mode="full")
                    old_targets = state.sample_targets()
                    step = state.translate(delta)
                    center = center[0]+delta[0], center[1]+delta[1]
                    state = step.footprint
                    self.assertEqual(state.center_q40, center)
                    self.assertEqual(state.sample_targets(), expected_step.footprint.sample_targets())
                    self.assertEqual(step.changed_samples,
                                     sum(a != b for a, b in zip(old_targets, state.sample_targets())))
                    self.assertMatchesFull(state)

    def test_boundary_prediction_accounts_for_accumulated_shift(self):
        state = TranslationFootprint.from_source(cell(19, -17), "coverage_up")
        velocity = (1000, -777)
        first = state.next_boundary(velocity)
        self.assertIsInstance(first, Fraction)
        self.assertGreater(first, 0)
        ticks = max(0, int(first)-1)
        shifted = state.translate((ticks*velocity[0], ticks*velocity[1])).footprint
        self.assertEqual(shifted.sample_targets(), state.sample_targets())
        self.assertEqual(shifted.next_boundary(velocity), first-ticks)
        self.assertIsNone(state.next_boundary((0, 0)))

    def test_large_jump_uses_full_and_explicit_full_is_available(self):
        state = TranslationFootprint.from_source(cell(3, -7), "coverage_down")
        large = state.translate((S//4, 0))
        self.assertEqual((large.mode, large.round_calls), ("full", 96))
        direct = state.translate((1, 0), mode="full")
        self.assertEqual((direct.mode, direct.round_calls), ("full", 96))
        self.assertMatchesFull(large.footprint)


if __name__ == "__main__":
    unittest.main()
