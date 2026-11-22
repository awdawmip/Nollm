"""Candidate geometry is evaluated through actual sampled coverage."""
import json
from math import pi, sqrt
import unittest

from nollm_core import GeometryAddress, Q16_ONE
from geometry.deformation import LayerMap, RadialTwist, SimilarityFrame, sampled_coverage
from geometry.pressure_evaluation import compare_pressure, evaluate_pressure


def cell(layer, q=0, r=0):
    return GeometryAddress("default_dream_v1", "default", layer, q, r)


def by_cell(report):
    return {GeometryAddress.from_mapping(item["cell"]): item for item in report["cells"]}


class PressureEvaluationTests(unittest.TestCase):
    def test_complete_source_mass_is_conserved_without_local_renormalization(self):
        lower = {cell(1, -7, 5): 3, cell(1, 1, 0): 2}
        report = evaluate_pressure({cell(0): 4}, lower, upper_layer=0, inventory_complete=True)
        self.assertEqual(report["distributed_support_q16"], 5 * Q16_ONE)
        for source, units in lower.items():
            allocated = sum(item["support_q16"] for item in report["allocations"]
                            if GeometryAddress.from_mapping(item["source"]) == source)
            self.assertEqual(allocated, units * Q16_ONE)
        self.assertEqual(sum(item["support_q16"] for item in report["cells"]), 5 * Q16_ONE)

    def test_translation_preserves_old_and_new_influence_regions(self):
        upper, lower = {cell(0): 4}, {cell(1): 4}
        identity = LayerMap()
        moved = LayerMap(SimilarityFrame(origin=(4 * sqrt(3), 0)))
        report = compare_pressure(
            upper, lower, upper_layer=0, before_upper_map=identity, before_lower_map=identity,
            after_lower_map=moved, inventory_complete=True, evaluation_cells=(cell(0, 4, 0),),
        )
        self.assertEqual(report["before"]["evaluation_region"], report["after"]["evaluation_region"])
        self.assertIn(cell(0), by_cell(report["after"]))
        self.assertIn(cell(0, 4, 0), by_cell(report["before"]))
        self.assertEqual(report["before"]["total_deficit_q16"], 0)
        self.assertEqual(report["after"]["total_deficit_q16"], 4 * Q16_ONE)
        self.assertEqual(report["after"]["distributed_support_q16"], 4 * Q16_ONE)
        self.assertEqual(sum(change["delta_support_q16"] for change in report["coverage_changes"]), 0)

    def test_relative_rotation_and_twist_change_allocations(self):
        upper, lower = {cell(0, 1, 0): 4}, {cell(1, 1, 0): 4}
        native = LayerMap.for_layer(1)
        candidates = [LayerMap(native.frame.rotate_about((0, 0), pi / 5)),
                      native.with_twist(RadialTwist(radius=6, angle=0.8))]
        for candidate in candidates:
            with self.subTest(candidate=candidate):
                report = compare_pressure(upper, lower, upper_layer=0, after_lower_map=candidate,
                                          inventory_complete=True)
                self.assertTrue(report["coverage_changes"])
                self.assertEqual(report["before"]["distributed_support_q16"], 4 * Q16_ONE)
                self.assertEqual(report["after"]["distributed_support_q16"], 4 * Q16_ONE)

    def test_common_area_preserving_twist_keeps_the_evaluation(self):
        upper = {cell(0): 6, cell(0, 1, 0): 3}
        lower = {cell(1): 2, cell(1, 1, 0): 3, cell(1, -2, -1): 1}
        first, second = LayerMap.for_layer(0), LayerMap.for_layer(1)
        twist = RadialTwist(center=(0.4, -0.2), radius=7, angle=1.3)
        report = compare_pressure(
            upper, lower, upper_layer=0, before_upper_map=first, before_lower_map=second,
            after_upper_map=first.with_twist(twist), after_lower_map=second.with_twist(twist),
            inventory_complete=True,
        )
        self.assertEqual(report["coverage_changes"], [])
        self.assertEqual(report["before"]["cells"], report["after"]["cells"])
        self.assertEqual(report["delta"]["total_deficit_q16"], 0)

    def test_same_total_deficit_can_have_a_better_pressure_distribution(self):
        source = cell(1)
        identity = LayerMap()
        shifted = LayerMap(SimilarityFrame(origin=(sqrt(3) / 2, 0)))
        # Every target of the candidate has demand. Spreading eight supplied
        # units balances those deficits without changing their total.
        upper = {member.target: 10 for member in sampled_coverage(source, 0, shifted, identity).members}
        report = compare_pressure(
            upper, {source: 8}, upper_layer=0,
            before_upper_map=identity, before_lower_map=identity,
            after_lower_map=shifted, inventory_complete=True,
        )
        self.assertEqual(report["delta"]["total_deficit_q16"], 0)
        self.assertLess(report["delta"]["max_known_pressure"], 0)
        self.assertNotEqual(report["before"]["cells"], report["after"]["cells"])
        self.assertTrue(report["advisory"])
        self.assertNotIn("approved", report)

    def test_partial_inventory_never_claims_a_total_field_improvement(self):
        report = compare_pressure(
            {cell(0): 8}, {cell(1): 2}, upper_layer=0,
            after_lower_map=LayerMap(SimilarityFrame(origin=(sqrt(3) / 2, 0))),
        )
        self.assertFalse(report["inventory_complete"])
        self.assertIsNone(report["delta"]["total_deficit_q16"])
        for side in (report["before"], report["after"]):
            self.assertIsNone(side["total_deficit_q16"])
            self.assertEqual(by_cell(side)[cell(0)]["score_kind"], "upper_estimate")
            missing = [item for item in side["cells"] if item["demand_units"] is None]
            self.assertTrue(missing)
            self.assertTrue(all(item["pressure"] is None for item in missing))

    def test_readout_is_json_and_leaves_inputs_unchanged(self):
        upper, lower = {cell(0): 2}, {cell(1): 1}
        before_upper, before_lower = dict(upper), dict(lower)
        report = compare_pressure(upper, lower, upper_layer=0, inventory_complete=True)
        self.assertEqual(json.loads(json.dumps(report)), report)
        self.assertEqual(report["coverage_changes"], [])
        self.assertEqual(upper, before_upper)
        self.assertEqual(lower, before_lower)

    def test_invalid_pair_or_count_is_rejected(self):
        for upper, lower, layer in (({cell(0): -1}, {}, 0),
                                    ({}, {cell(2): 1}, 0),
                                    ({}, {}, 64)):
            with self.assertRaises(ValueError):
                evaluate_pressure(upper, lower, upper_layer=layer)


if __name__ == "__main__":
    unittest.main()
