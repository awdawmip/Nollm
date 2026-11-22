"""Adaptive execution preserves the full rational sampling and pressure contract."""
from dataclasses import replace
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from nollm_core import GeometryAddress, Q16_ONE
from geometry.adaptive_rational_kernel import compile_adaptive_pair
from geometry.rational_coverage import (
    compare_rational_pressure, evaluate_rational_pressure, nearest_axial_rational,
    rational_sample_numerators, rational_sample_offsets, sampled_rational_coverage,
)
from geometry.rational_geometry import (
    RationalAffine, RationalLayerMap, RationalRadialTwist, rational_from_mapping,
)


def cell(layer, q=0, r=0):
    return GeometryAddress("default_dream_v1", "default", layer, q, r)


def exact_targets(source, target, q=0, r=0):
    return tuple(nearest_axial_rational(*target.inverse(source.forward((q+dq, r+dr))))
                 for dq, dr in rational_sample_offsets())


def distinct_maps():
    source = RationalLayerMap(
        RationalAffine.similarity("5/4", "1/7", origin=("1/11", "-2/13")),
        (RationalRadialTwist((0, 0), 9, "1/5"),))
    target = RationalLayerMap(
        RationalAffine.similarity("7/6", "-1/9", origin=("-1/5", "2/7"),
                                  local_anchor=("1/13", "-1/17")),
        (RationalRadialTwist(("1/5", 0), 9, "-1/7"),))
    return source, target


def translate_world(mapping, anchor):
    def shifted(point):
        return tuple(value+offset for value, offset in zip(point, anchor))
    return RationalLayerMap(replace(mapping.frame, origin=shifted(mapping.frame.origin)),
                            tuple(replace(twist, center=shifted(twist.center))
                                  for twist in mapping.twists))


def one_hit_edge_source(exponent):
    """One sample is at (1/2+2^-exponent,0), fixed by an active tiny twist."""
    small = RationalAffine.similarity("1/10", "1/7")
    tip = max((small.forward(point) for point in rational_sample_offsets()),
              key=lambda point: 2*point[0]+point[1])
    center = F(1, 2)+F(1, 1 << exponent), F(0)
    frame = replace(small, origin=(center[0]-tip[0], -tip[1]))
    # The radius is smaller than the distance to every other sample. The tip
    # stays fixed at the twist center; the other 95 samples are outside.
    return RationalLayerMap(frame, (RationalRadialTwist(center, F(1, 1 << 20), "1/7"),))


class AdaptiveRationalKernelTests(unittest.TestCase):
    def test_distinct_twists_preserve_each_sample_in_both_relative_directions(self):
        source, target = distinct_maps()
        for first, second in ((source, target), (target, source)):
            kernel = compile_adaptive_pair(first, second)
            for q, r in ((0, 0), (-1, 1), (2, -1)):
                with self.subTest(q=q, r=r, source=first):
                    actual = kernel.targets(q, r, rational_sample_numerators(), 36)
                    self.assertEqual(actual, exact_targets(first, second, q, r))

    def test_alternating_centers_preserve_order_and_all_labeled_targets(self):
        first = RationalRadialTwist((0, 0), 9, "1/5")
        second = RationalRadialTwist(("1/5", "-1/7"), 9, "-1/7")
        source = RationalLayerMap(RationalAffine.similarity("4/5", "1/11"),
                                  (first, second, first))
        target = RationalLayerMap(RationalAffine(origin=("1/13", "-1/17")))
        result = compile_adaptive_pair(source, target).targets_with_stats(
            0, 0, rational_sample_numerators(), 36)
        self.assertEqual(result.targets, exact_targets(source, target))
        self.assertEqual(result.stats["sample_count"], 96)
        self.assertEqual(sum(result.stats["certified_by_bits"].values())
                         + result.stats["exact_fallback"] + result.stats["affine_exact"], 96)

    def test_initial_zero_bits_refines_and_only_unresolved_points_repeat(self):
        source, target = distinct_maps()
        result = compile_adaptive_pair(source, target, initial_bits=0, max_bits=32).targets_with_stats(
            0, 0, rational_sample_numerators(), 36)
        self.assertEqual(result.targets, exact_targets(source, target))
        attempted = result.stats["attempted_by_bits"]
        certified = result.stats["certified_by_bits"]
        self.assertEqual(attempted[0], 96)
        self.assertTrue(any(bits > 0 for bits in attempted))
        remaining = 96
        for bits in sorted(attempted):
            self.assertEqual(attempted[bits], remaining)
            remaining -= certified.get(bits, 0)
        self.assertEqual(remaining, result.stats["exact_fallback"])

    def test_precision_cap_falls_back_for_a_sub_q40_boundary_point(self):
        denominator = 1 << 80
        point = F(1, 2)+F(1, denominator), F(0)
        source = RationalLayerMap(twists=(RationalRadialTwist(point, 1, "1/7"),))
        result = compile_adaptive_pair(source, RationalLayerMap(),
                                       initial_bits=0, max_bits=0).targets_with_stats(
            0, 0, ((denominator//2+1, 0),), denominator)
        self.assertEqual(result.targets, ((1, 0),))
        self.assertEqual(result.stats["exact_fallback"], 1)

    def test_exact_ties_retain_absolute_half_even_parity(self):
        for numerator, expected in ((1, (0, 0)), (3, (2, 0)),
                                    (-1, (0, 0)), (-3, (-2, 0))):
            point = F(numerator, 2), F(0)
            source = RationalLayerMap(twists=(RationalRadialTwist(point, 1, "1/7"),))
            result = compile_adaptive_pair(source, RationalLayerMap(),
                                           initial_bits=0, max_bits=8).targets(
                0, 0, ((numerator, 0),), 2)
            self.assertEqual(result, (expected,))

    def test_common_outer_suffix_cancels_without_changing_inner_twists(self):
        source, target = distinct_maps()
        common = (RationalRadialTwist(("2/7", "-1/9"), 6, "1/11"),
                  RationalRadialTwist(("-1/5", "1/3"), 8, "-1/13"))
        first = replace(source, twists=source.twists+common)
        second = replace(target, twists=target.twists+common)
        result = compile_adaptive_pair(first, second).targets_with_stats(
            0, 0, rational_sample_numerators(), 36)
        self.assertEqual(result.targets, exact_targets(source, target))
        self.assertEqual(result.stats["cancelled_common_twists"], 2)
        self.assertEqual(result.stats["affine_exact"], 0)
        # One unreduced full rational composition also checks the suffix order.
        point = F(1, 36), F(-2, 36)
        self.assertEqual(second.inverse(first.forward(point)), target.inverse(source.forward(point)))

    def test_equal_outer_twists_keep_the_exact_integer_affine_shortcut(self):
        source, target = distinct_maps()
        target = replace(target, twists=source.twists)
        expected = exact_targets(source, target)
        with patch.object(RationalRadialTwist, "_map", side_effect=AssertionError("cancelled twist")):
            result = compile_adaptive_pair(source, target).targets_with_stats(
                0, 0, rational_sample_numerators(), 36)
        self.assertEqual(result.targets, expected)
        self.assertEqual(result.stats["affine_exact"], 96)
        self.assertEqual(result.stats["attempted_by_bits"], {})
        self.assertEqual(result.stats["exact_fallback"], 0)

    def test_certified_nonlinear_stencil_does_not_evaluate_exact_twists(self):
        source = RationalLayerMap(twists=(RationalRadialTwist(("1/7", "-2/13"), 9, "1/31"),))
        target = RationalLayerMap()
        expected = exact_targets(source, target)
        with patch.object(RationalRadialTwist, "_map", side_effect=AssertionError("unneeded exact twist")):
            result = compile_adaptive_pair(source, target).targets_with_stats(
                0, 0, rational_sample_numerators(), 36)
        self.assertEqual(result.targets, expected)
        self.assertEqual(result.stats["exact_fallback"], 0)
        self.assertEqual(sum(result.stats["certified_by_bits"].values()), 96)

    def test_huge_common_world_anchor_preserves_nonlinear_coverage(self):
        source, target = distinct_maps()
        huge = 1 << 160
        shifted_source = translate_world(source, (huge, -huge))
        shifted_target = translate_world(target, (huge, -huge))
        expected = sampled_rational_coverage(cell(1, 1, -1), 0, source, target, mode="reference")
        actual = sampled_rational_coverage(cell(1, 1, -1), 0, shifted_source, shifted_target,
                                           mode="adaptive")
        self.assertEqual(actual, expected)


class AdaptiveRationalCoverageTests(unittest.TestCase):
    def test_one_hit_edge_survives_refinement_and_forced_fallback(self):
        source, target = one_hit_edge_source(60), RationalLayerMap()
        expected = sampled_rational_coverage(cell(1), 0, source, target, mode="reference")
        self.assertEqual({(m.target.q, m.target.r): m.hit_count for m in expected.members},
                         {(0, 0): 95, (1, 0): 1})
        for cap in (16, 128):
            with self.subTest(max_bits=cap):
                actual = sampled_rational_coverage(cell(1), 0, source, target,
                                                   mode="adaptive", max_bits=cap)
                self.assertEqual(actual, expected)
        kernel = compile_adaptive_pair(source, target, max_bits=16)
        self.assertGreaterEqual(kernel.targets_with_stats(
            0, 0, rational_sample_numerators(), 36).stats["exact_fallback"], 1)

    def test_coverage_keeps_exact_shares_q16_and_json(self):
        source, target = distinct_maps()
        expected = sampled_rational_coverage(cell(-1, -1, 0), 0, source, target, mode="reference")
        actual = sampled_rational_coverage(cell(-1, -1, 0), 0, source, target, mode="adaptive",
                                           initial_bits=4, max_bits=32)
        self.assertEqual(actual.to_mapping(), expected.to_mapping())
        self.assertEqual(sum(member.hit_count for member in actual.members), 96)
        self.assertEqual(sum(member.weight for member in actual.members), 1)
        self.assertEqual(sum(member.weight_q16 for member in actual.members), Q16_ONE)

    def test_complete_inventory_pressure_is_identical_after_nonlinear_execution(self):
        lower_map, upper_map = distinct_maps()
        upper = {cell(0): 4, cell(0, 1, -1): 2}
        lower = {cell(1): 3, cell(1, 1, -1): 2, cell(1, -1, 1): 0}
        kwargs = dict(upper_layer=0, upper_map=upper_map, lower_map=lower_map,
                      inventory_complete=True, kappa="2/3")
        expected = evaluate_rational_pressure(upper, lower, **kwargs, mode="reference")
        actual = evaluate_rational_pressure(upper, lower, **kwargs, mode="adaptive",
                                             initial_bits=4, max_bits=16)
        self.assertEqual(actual, expected)
        self.assertEqual(rational_from_mapping(actual["distributed_support"]), 5)

    def test_candidate_comparison_retains_old_new_union_and_partial_unknowns(self):
        before, upper_map = distinct_maps()
        after = replace(before, frame=replace(before.frame, origin=(4, 0)))
        upper, lower = {cell(0): 5}, {cell(1): 2}
        for complete in (False, True):
            kwargs = dict(upper_layer=0, before_upper_map=upper_map,
                          before_lower_map=before, after_lower_map=after,
                          inventory_complete=complete, evaluation_cells=(cell(0, -5, 0),))
            expected = compare_rational_pressure(upper, lower, **kwargs, mode="reference")
            actual = compare_rational_pressure(upper, lower, **kwargs, mode="adaptive",
                                               initial_bits=0, max_bits=16)
            self.assertEqual(actual, expected)
            self.assertTrue(actual["coverage_changes"])
            self.assertEqual(actual["before"]["evaluation_region"], actual["after"]["evaluation_region"])
            self.assertEqual(sum(rational_from_mapping(change["delta_support"])
                                 for change in actual["coverage_changes"]), 0)
            if not complete:
                self.assertIsNone(actual["delta"]["total_deficit"])
                unknown = [item for item in actual["after"]["cells"] if item["demand_units"] is None]
                self.assertTrue(unknown)
                self.assertTrue(all(item["pressure_exact"] is None and item["pressure"] is None
                                    for item in unknown))


if __name__ == "__main__":
    unittest.main()
