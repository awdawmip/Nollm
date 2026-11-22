"""Exact residual classification and maintained-state checks for Q40 motion."""
from collections import Counter
from fractions import Fraction
from pathlib import Path
import random
import sys
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(REPO / "packages/nollm-core/src"),
                str(Path(__file__).resolve().parents[1])]
import motion
from motion import NORMALS, Q40_ONE as S, TranslationFootprint
from nollm_core import GeometryAddress, coverage_stencil_q40, nearest_axial_q40, normalize_q16_weights


def source(q=19, r=-17):
    return GeometryAddress("default_dream_v1", "default", 0, q, r)


def direct(direction, center):
    offsets = coverage_stencil_q40(source(0, 0), direction).offsets_q40
    targets = tuple(nearest_axial_q40(center[0] + q, center[1] + r) for q, r in offsets)
    counts = sorted(Counter(targets).items())
    weights = normalize_q16_weights([count for _, count in counts])
    return targets, tuple((q, r, count, weight)
                          for ((q, r), count), weight in zip(counts, weights))


class ResidualEventTests(unittest.TestCase):
    def assertExact(self, state):
        targets, counts = direct(state.direction, state.center_q40)
        self.assertEqual(state.sample_targets(), targets)
        self.assertEqual(state.counts_q16(), counts)
        self.assertEqual(sum(row[2] for row in counts), 96)
        self.assertEqual(sum(row[3] for row in counts), 65536)
        self.assertEqual(state.anchor[0] % 2, 0)
        self.assertEqual(state.anchor[1] % 2, 0)

    def assertGroupsExact(self, state):
        self.assertEqual(state._minima,
                         tuple(min(row[h] for row in state._margins) for h in range(6)))
        if state._events is None:
            self.assertIsNone(state._groups)
            return
        for (hq, hr), events, grouped in zip(NORMALS[:3], state._events, state._groups):
            observed = {}
            for i, (q, r) in enumerate(state._targets):
                key = hq*q + hr*r
                samples, ranks = observed.get(key, (0, 0))
                observed[key] = samples | (1 << i), ranks | events.rank_bits[i]
            self.assertEqual(grouped, observed)

    def test_only_inclusive_face_residuals_reach_rounder(self):
        rng = random.Random(782451)
        for direction in ("coverage_up", "coverage_down"):
            state = TranslationFootprint.from_source(source(), direction)
            crossings = 0
            for _ in range(200):
                delta = (rng.randrange(-S//200, S//200), rng.randrange(-S//200, S//200))
                shift = state._shift[0] + delta[0], state._shift[1] + delta[1]
                projections = tuple(hq*shift[0] + hr*shift[1] for hq, hr in NORMALS)
                expected = {i for i, margins in enumerate(state._margins)
                            if any(p >= m for p, m in zip(projections, margins))}
                old = state
                with patch.object(motion, "nearest_axial_q40", wraps=nearest_axial_q40) as rounder:
                    step = state.translate(delta)
                    self.assertEqual(rounder.call_count, len(expected))
                    self.assertEqual(step.round_calls, len(expected))
                    self.assertEqual({call.args for call in rounder.call_args_list},
                                     {(old._points[i][0] + shift[0], old._points[i][1] + shift[1])
                                      for i in expected})
                state = step.footprint
                self.assertIs(state._points, old._points)
                if old._events is not None:
                    self.assertIs(state._events, old._events)
                for i, target in enumerate(state._targets):
                    if target == old._targets[i]:
                        self.assertIs(state._margins[i], old._margins[i])
                crossings += step.mode == "crossings"
                self.assertExact(state)
                self.assertGroupsExact(state)
            self.assertGreater(crossings, 0)

    def test_boundary_equalities_and_duplicate_labels_are_not_dropped(self):
        # Equal event coordinates retain all 96 sample identities, even when
        # the tie rule keeps their current target rather than crossing it.
        state = TranslationFootprint._from_center("coverage_up", (0, 0),
                                                  ((S//2-1, 0),) * 96)
        at_boundary = state.translate((1, 0))
        self.assertEqual(at_boundary.round_calls, 96)
        self.assertEqual(at_boundary.footprint.sample_targets(), ((0, 0),) * 96)
        self.assertEqual(at_boundary.changed_samples, 0)
        beyond = at_boundary.footprint.translate((1, 0))
        self.assertEqual(beyond.round_calls, 96)
        self.assertEqual(beyond.changed_samples, 96)
        self.assertEqual(beyond.footprint.sample_targets(), ((1, 0),) * 96)
        self.assertEqual(beyond.footprint.counts_q16(), ((1, 0, 96, 65536),))
        reverse = beyond.footprint.translate((-1, 0))
        self.assertEqual(reverse.footprint.sample_targets(), ((0, 0),) * 96)
        self.assertGroupsExact(reverse.footprint)

    def test_same_present_readout_keeps_distinct_future_phases(self):
        ox, oy = coverage_stencil_q40(source(), "coverage_down").offsets_q40[0]
        left = TranslationFootprint.from_center_q40("coverage_down", (S//2-ox-2, -oy))
        right = TranslationFootprint.from_center_q40("coverage_down", (S//2-ox-1, -oy))
        self.assertEqual(left.sample_targets(), right.sample_targets())
        self.assertEqual(left.counts_q16(), right.counts_q16())
        left_after = left.translate((2, 0)).footprint
        right_after = right.translate((2, 0)).footprint
        self.assertNotEqual(left_after.sample_targets(), right_after.sample_targets())
        self.assertExact(left_after)
        self.assertExact(right_after)

    def test_branches_share_static_arrays_without_mutating_prior_membership(self):
        state = TranslationFootprint.from_source(source(), "coverage_up")
        for _ in range(64):
            state = state.translate((S//1000, -S//2000)).footprint
            if state._events is not None:
                break
        self.assertIsNotNone(state._events)
        before = (state.sample_targets(), state.counts_q16(), tuple(dict(g) for g in state._groups))
        left, right = state, state
        for _ in range(128):
            left = left.translate((S//1000, -S//2000)).footprint
            right = right.translate((-S//2000, S//1000)).footprint
        self.assertEqual((state.sample_targets(), state.counts_q16(), state._groups), before)
        self.assertIs(left._events, state._events)
        self.assertIs(right._events, state._events)
        self.assertExact(left)
        self.assertExact(right)
        self.assertGroupsExact(left)
        self.assertGroupsExact(right)

    def test_accumulated_small_motion_and_boundary_prediction(self):
        state = TranslationFootprint.from_source(source(-17, 23), "coverage_down")
        for i in range(640):
            state = state.translate((S//128, -S//256)).footprint
            if i % 31 == 0:
                velocity = (1234567, -765432)
                times = []
                for (hq, hr), margin in zip(NORMALS, state._minima):
                    speed = hq*velocity[0] + hr*velocity[1]
                    if speed > 0:
                        times.append(Fraction(margin-hq*state._shift[0]-hr*state._shift[1], speed))
                self.assertEqual(state.next_boundary(velocity), min(times))
                self.assertGreaterEqual(state.next_boundary(velocity), 0)
                self.assertExact(state)
                self.assertGroupsExact(state)
        self.assertGreater(state._shift[0], S)
        self.assertExact(state)

    def test_large_signed_coordinates_full_fallback_and_even_anchors(self):
        # These raw diagnostic coordinates exceed admission; the motion API
        # does not persist them or change the product storage-domain contract.
        for direction in ("coverage_up", "coverage_down"):
            for sign in (-1, 1):
                center = sign*(1 << 120) + S//2, -sign*(1 << 119) - 17
                state = TranslationFootprint.from_center_q40(direction, center)
                for delta in ((0, 0), (2*S, -4*S), (1, -1), (S//128, 0),
                              (S//4, -S//3), (S, 0), (-S, 0), (7, -19)):
                    old = state.sample_targets()
                    step = state.translate(delta)
                    state = step.footprint
                    center = center[0] + delta[0], center[1] + delta[1]
                    self.assertEqual(state.center_q40, center)
                    self.assertEqual(step.changed_samples,
                                     sum(a != b for a, b in zip(old, state.sample_targets())))
                    self.assertExact(state)
                    self.assertGroupsExact(state)
                explicit = state.translate((0, 0), mode="full")
                self.assertEqual((explicit.mode, explicit.round_calls), ("full", 96))
                self.assertEqual(explicit.changed_samples, 0)
                self.assertIs(explicit.footprint._events, state._events)
                self.assertExact(explicit.footprint)

    def test_unknown_mode_is_rejected(self):
        state = TranslationFootprint.from_source(source(), "coverage_up")
        with self.assertRaisesRegex(ValueError, "mode"):
            state.translate((1, 2), mode="sampled")


if __name__ == "__main__":
    unittest.main()
