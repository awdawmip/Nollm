"""Geometry reuse preserves actual coverage and current-inventory pressure."""
from collections import Counter
import json
from math import nextafter, pi, sqrt
import random
import unittest
from unittest.mock import patch

from nollm_core import (
    GeometryAddress, Q16_ONE, coverage_sample_offsets_q40,
    nearest_axial_q40, normalize_q16_weights,
)
from geometry import deformation
from geometry.deformation import (
    LayerMap, RadialTwist, SimilarityFrame, sampled_coverage, source_world_samples,
)
from geometry.pressure_evaluation import compare_pressure, evaluate_pressure


def cell(layer, q=0, r=0):
    return GeometryAddress("default_dream_v1", "default", layer, q, r)


def result_only(report):
    return {key: value for key, value in report.items() if key != "work"}


def original_interleaved_reference(source, target_layer, source_map, target_map):
    """Retain the original source->target arithmetic order as a separate oracle."""
    scale = 1 << 40
    center = sqrt(3) * (source.q + source.r / 2), 1.5 * source.r
    targets = []
    for dx, dy in coverage_sample_offsets_q40():
        point = center[0] + dx / scale, center[1] + dy / scale
        x, y = target_map.inverse(source_map.forward(point))
        targets.append(nearest_axial_q40(round((x / sqrt(3) - y / 3) * scale),
                                         round((2 * y / 3) * scale)))
    counts = sorted(Counter(targets).items())
    weights = normalize_q16_weights([count for _, count in counts])
    return tuple((q, r, count, weight)
                 for ((q, r), count), weight in zip(counts, weights))


class PressureReuseTests(unittest.TestCase):
    def compare_modes(self, upper, lower, **options):
        auto = compare_pressure(upper, lower, upper_layer=0, mode="auto", **options)
        full = compare_pressure(upper, lower, upper_layer=0, mode="full", **options)
        self.assertEqual(result_only(auto), result_only(full))
        return auto, full

    def test_same_geometry_reuses_coverage_and_work_counts_real_round_calls(self):
        upper = {cell(0): 8, cell(0, 2, -1): 4}
        lower = {cell(1): 2, cell(1, 2, -1): 3, cell(1, -1, 0): 0}
        with patch.object(deformation, "nearest_axial_q40", wraps=nearest_axial_q40) as rounder:
            auto = compare_pressure(upper, lower, upper_layer=0, inventory_complete=True)
            self.assertEqual(rounder.call_count, auto["work"]["round_calls"])
        with patch.object(deformation, "nearest_axial_q40", wraps=nearest_axial_q40) as rounder:
            full = compare_pressure(upper, lower, upper_layer=0,
                                    inventory_complete=True, mode="full")
            self.assertEqual(rounder.call_count, full["work"]["round_calls"])
        self.assertEqual(result_only(auto), result_only(full))
        self.assertEqual(auto["work"]["coverage_evaluations"], 2)
        self.assertEqual(auto["work"]["same_map_reuses"], 2)
        self.assertEqual(auto["work"]["peak_cached_source_samples"], 96)
        self.assertEqual(auto["work"]["round_calls"], 192)
        self.assertEqual(full["work"]["round_calls"], 384)

    def test_local_target_twist_skips_only_sources_outside_its_support_box(self):
        lower = {cell(1, q, 0): q + 1 for q in range(24)}
        upper = {cell(0, q, 0): 10 for q in range(12)}
        candidate = LayerMap.for_layer(0).with_twist(RadialTwist(radius=3, angle=1.1))
        auto, full = self.compare_modes(upper, lower, after_upper_map=candidate,
                                        inventory_complete=True)
        self.assertGreater(auto["work"]["outside_twist_reuses"], 18)
        self.assertEqual(auto["work"]["peak_cached_source_samples"], 96)
        self.assertLess(auto["work"]["round_calls"], full["work"]["round_calls"])
        self.assertTrue(auto["coverage_changes"])
        self.assertEqual(auto["before"]["distributed_support_q16"], sum(lower.values()) * Q16_ONE)
        self.assertEqual(auto["after"]["distributed_support_q16"], sum(lower.values()) * Q16_ONE)

    def test_literal_appended_source_and_target_suffixes_preserve_old_maps(self):
        prefix = RadialTwist(center=(0.1, -0.3), radius=5, angle=0.2)
        first = LayerMap.for_layer(0).with_twist(prefix)
        second = LayerMap.for_layer(1).with_twist(prefix)
        far = (RadialTwist(center=(100, 70), radius=1, angle=1.1),
               RadialTwist(center=(-100, 0), radius=4, angle=-0.4))
        candidate_upper = first.with_twist(far[0]).with_twist(far[1])
        candidate_lower = second.with_twist(far[1]).with_twist(far[0])
        lower = {cell(1): 2, cell(1, 1, 0): 1}
        auto, _ = self.compare_modes({cell(0): 4}, lower,
            before_upper_map=first, before_lower_map=second,
            after_upper_map=candidate_upper, after_lower_map=candidate_lower)
        self.assertEqual(auto["work"]["outside_twist_reuses"], 2)
        self.assertEqual(auto["work"]["coverage_evaluations"], 2)
        self.assertEqual(auto["coverage_changes"], [])
        self.assertEqual(auto["after"]["maps"]["upper"], candidate_upper.to_mapping())

    def test_exact_box_boundary_reuses_and_one_float_step_inside_recomputes(self):
        source = cell(1)
        identity = LayerMap()
        points = tuple(source_world_samples(source, identity))
        right = max(x for x, _ in points)
        radius = 1.0
        center = right + radius
        self.assertEqual(right - center, -radius)
        boundary = identity.with_twist(RadialTwist((center, 0), radius, 1.0))
        options = {"before_upper_map": identity, "before_lower_map": identity}
        auto, _ = self.compare_modes({cell(0): 4}, {source: 2},
                                     after_upper_map=boundary, **options)
        self.assertEqual(auto["work"]["outside_twist_reuses"], 1)
        inside = identity.with_twist(RadialTwist((nextafter(center, -float("inf")), 0), radius, 1.0))
        auto, _ = self.compare_modes({cell(0): 4}, {source: 2},
                                     after_upper_map=inside, **options)
        self.assertEqual(auto["work"]["outside_twist_reuses"], 0)
        self.assertEqual(auto["work"]["coverage_evaluations"], 2)

    def test_other_map_changes_do_not_inherit_append_only_exclusion(self):
        old_twist = RadialTwist((100, 0), 1, 0.4)
        before = LayerMap.for_layer(0).with_twist(old_twist)
        variants = [LayerMap.for_layer(0),
                    LayerMap.for_layer(0).with_twist(old_twist.with_center((0, 0))),
                    LayerMap(before.frame.rotate_about((0, 0), pi / 7), before.twists)]
        for after in variants:
            with self.subTest(after=after):
                auto, _ = self.compare_modes({cell(0): 3}, {cell(1): 2},
                                             before_upper_map=before, after_upper_map=after)
                self.assertEqual(auto["work"]["outside_twist_reuses"], 0)
                self.assertEqual(auto["work"]["coverage_evaluations"], 2)
                self.assertEqual(auto["work"]["source_sample_maps"], 96)
                self.assertEqual(auto["work"]["source_sample_reuses"], 96)

        source_change = LayerMap(LayerMap.for_layer(1).frame.rotate_about((0, 0), pi / 9))
        auto, full = self.compare_modes({cell(0): 3}, {cell(1): 2}, after_lower_map=source_change)
        self.assertFalse(auto["work"]["reuse_enabled"])
        self.assertEqual(auto["work"]["peak_cached_source_samples"], 0)
        self.assertEqual(auto["work"]["source_sample_maps"], full["work"]["source_sample_maps"])

    def test_new_request_uses_current_inventory_and_partial_unknowns(self):
        first, _ = self.compare_modes({cell(0): 8}, {cell(1): 1})
        second, _ = self.compare_modes({cell(0): 9}, {cell(1): 4, cell(1, 2, 0): 1})
        empty, _ = self.compare_modes({cell(0): 9}, {})
        self.assertEqual(first["before"]["distributed_support_q16"], Q16_ONE)
        self.assertEqual(second["before"]["distributed_support_q16"], 5 * Q16_ONE)
        self.assertEqual(empty["before"]["distributed_support_q16"], 0)
        self.assertEqual(second["work"]["coverage_evaluations"], 2)
        self.assertEqual(empty["work"]["coverage_evaluations"], 0)
        for report in (first, second, empty):
            self.assertIsNone(report["before"]["total_deficit_q16"])
            self.assertIsNone(report["delta"]["total_deficit_q16"])
            for item in report["before"]["cells"]:
                self.assertEqual(item["score_kind"], "demand_unknown" if item["demand_units"] is None
                                 else "upper_estimate")

    def test_source_sample_retention_matches_original_arithmetic(self):
        rng = random.Random(852026)
        for index in range(24):
            source = cell(1, rng.randint(-20000, 20000), rng.randint(-20000, 20000))
            lower = LayerMap(SimilarityFrame((0.1, -0.3), scale=0.9, angle=index / 13))
            upper = LayerMap(SimilarityFrame((-0.2, 0.5), scale=1.3, angle=-index / 19),
                             (RadialTwist((0.2, -0.4), 30000, 0.7),))
            expected = original_interleaved_reference(source, 0, lower, upper)
            retained = tuple(source_world_samples(source, lower))
            actual = sampled_coverage(source, 0, lower, upper, world_samples=retained)
            self.assertEqual(tuple((m.target.q, m.target.r, m.hit_count, m.weight_q16)
                                   for m in actual.members), expected)
            self.assertEqual(actual, sampled_coverage(source, 0, lower, upper))

    def test_work_is_json_and_full_mode_remains_available_for_single_evaluation(self):
        options = {"upper_layer": 0, "inventory_complete": True}
        auto = evaluate_pressure({cell(0): 4}, {cell(1): 2}, **options)
        full = evaluate_pressure({cell(0): 4}, {cell(1): 2}, mode="full", **options)
        self.assertEqual(result_only(auto), result_only(full))
        self.assertEqual(auto, json.loads(json.dumps(auto)))
        self.assertEqual(full["work"]["round_calls"], 96)
        with self.assertRaisesRegex(ValueError, "mode"):
            compare_pressure({}, {}, upper_layer=0, mode="unknown")


if __name__ == "__main__":
    unittest.main()
