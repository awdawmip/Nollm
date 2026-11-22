"""Exact rational geometry decisions and material support, independent of Q16."""
from fractions import Fraction
import json
import unittest
from unittest.mock import patch

from nollm_access import pressure_score
from nollm_core import GeometryAddress, Q16_ONE, nearest_axial_q40, normalize_q16_weights
from geometry.rational_geometry import (
    RationalAffine, RationalLayerMap, RationalRadialTwist, rational_from_mapping,
)
from geometry.rational_coverage import (
    RATIONAL_COVERAGE_CONTRACT_ID, compare_rational_pressure,
    evaluate_rational_pressure, nearest_axial_rational, pressure_display,
    rational_pressure_score, rational_sample_offsets, sampled_rational_coverage,
)


def cell(layer, q=0, r=0):
    return GeometryAddress("default_dream_v1", "default", layer, q, r)


def norm(q, r):
    return q * q + q * r + r * r


def by_cell(report):
    return {GeometryAddress.from_mapping(item["cell"]): item for item in report["cells"]}


class RationalCoverageTests(unittest.TestCase):
    def test_exact_stencil_has_96_distinct_interior_equal_area_centroids(self):
        points = rational_sample_offsets()
        self.assertEqual(len(points), 96)
        self.assertEqual(len(set(points)), 96)
        self.assertEqual(sum(q for q, _ in points), 0)
        self.assertEqual(sum(r for _, r in points), 0)
        self.assertEqual(set(points), {(-q, -r) for q, r in points})
        for q, r in points:
            self.assertEqual(36 % q.denominator, 0)
            self.assertEqual(36 % r.denominator, 0)
            self.assertLess(max(abs(2 * q + r), abs(q + 2 * r), abs(r - q)), 1)

    def test_rounder_agrees_with_independent_nearest_lattice_search(self):
        for qn in range(-17, 18):
            for rn in range(-17, 18):
                q, r = Fraction(qn, 7), Fraction(rn, 9)
                target = nearest_axial_rational(q, r)
                fq, fr = q.numerator // q.denominator, r.numerator // r.denominator
                candidates = [(a, b) for a in range(fq - 1, fq + 3)
                               for b in range(fr - 1, fr + 3)]
                best = min(norm(q - a, r - b) for a, b in candidates)
                self.assertEqual(norm(q - target[0], r - target[1]), best)
        for q, expected in ((Fraction(1, 2), (0, 0)), (Fraction(3, 2), (2, 0)),
                            (Fraction(-1, 2), (0, 0)), (Fraction(-3, 2), (-2, 0))):
            self.assertEqual(nearest_axial_rational(q, 0), expected)

    def test_sub_q40_boundary_residual_is_not_quantized_away(self):
        q = Fraction(1, 2) + Fraction(1, 1 << 60)
        self.assertEqual(nearest_axial_rational(q, 0), (1, 0))
        # Existing quantize-then-round interpretation has a different input.
        self.assertEqual(nearest_axial_q40(round(q * (1 << 40)), 0), (0, 0))
        self.assertEqual(nearest_axial_rational(q - Fraction(2, 1 << 60), 0), (0, 0))

    def test_same_maps_exactly_recover_source_cell_including_twists(self):
        maps = [RationalLayerMap(), RationalLayerMap(
            RationalAffine.similarity(scale="3/2", rotation_parameter="1/7", origin=(5, -3)),
            (RationalRadialTwist(center=(5, -3), radius_squared=8, strength="1/5"),))]
        for mapping in maps:
            for layer, q, r in ((0, 0, 0), (1, 2, -1), (-3, -1, 1)):
                result = sampled_rational_coverage(cell(layer, q, r), layer + 1, mapping, mapping)
                self.assertEqual([(m.target.q, m.target.r, m.hit_count, m.weight, m.weight_q16)
                                  for m in result.members], [(q, r, 96, Fraction(1), Q16_ONE)])

    def test_common_huge_anchor_keeps_one_unit_relative_offset(self):
        identity = RationalLayerMap()
        shift = RationalLayerMap(RationalAffine(origin=(1, 0)))
        big = 1 << 100
        huge_target = RationalLayerMap(RationalAffine(origin=(big, big)))
        huge_source = RationalLayerMap(RationalAffine(origin=(big + 1, big)))
        expected = sampled_rational_coverage(cell(0), 1, shift, identity)
        actual = sampled_rational_coverage(cell(0), 1, huge_source, huge_target)
        self.assertEqual(actual, expected)
        self.assertEqual(actual.members[0].target, cell(1, 1, 0))

    def test_full_source_shares_and_json_preserve_exact_fractions(self):
        mapping = RationalLayerMap(RationalAffine(origin=("1/7", "1/11")))
        result = sampled_rational_coverage(cell(1), 0, mapping, RationalLayerMap())
        self.assertGreater(len(result.members), 1)
        self.assertEqual(sum(m.hit_count for m in result.members), 96)
        self.assertEqual(sum(m.weight for m in result.members), 1)
        self.assertEqual(sum(m.weight_q16 for m in result.members), Q16_ONE)
        encoded = json.loads(json.dumps(result.to_mapping()))
        self.assertEqual(encoded["contract_id"], RATIONAL_COVERAGE_CONTRACT_ID)
        for actual, member in zip(encoded["members"], result.members):
            self.assertEqual(rational_from_mapping(actual["weight"]), member.weight)

    def test_common_world_twist_cancels_before_coverage_readout(self):
        source = RationalLayerMap(RationalAffine.similarity(scale="3/4", rotation_parameter="1/11"))
        target = RationalLayerMap(RationalAffine(origin=("1/7", 0)))
        twist = RationalRadialTwist(center=(0, 0), radius_squared=5, strength="1/9")
        expected = sampled_rational_coverage(cell(1), 0, source, target)
        actual = sampled_rational_coverage(cell(1), 0, source.with_twist(twist), target.with_twist(twist))
        self.assertEqual(actual, expected)

    def test_invalid_target_domain_fails_explicitly(self):
        identity = RationalLayerMap()
        for target in (0, 2, 65):
            with self.assertRaises(ValueError):
                sampled_rational_coverage(cell(0), target, identity, identity)

    def test_integer_auto_and_fraction_reference_have_identical_outputs(self):
        first = RationalLayerMap(RationalAffine.similarity("5/4", "1/7", origin=("2/9", "-3/11")))
        second = RationalLayerMap(RationalAffine.similarity("7/6", "-1/5", local_anchor=("1/3", "-2/7")))
        twist = RationalRadialTwist(radius_squared=2, strength="1/9")
        pairs = ((first, second), (first.with_twist(twist), second.with_twist(twist)),
                 (first.with_twist(twist), second))
        for source_map, target_map in pairs:
            for q, r in ((0, 0), (1, -2), (-3, 2)):
                args = cell(1, q, r), 0, source_map, target_map
                self.assertEqual(sampled_rational_coverage(*args, mode="auto"),
                                 sampled_rational_coverage(*args, mode="reference"))
        # A common exact world transform is removed before per-sample evaluation.
        with patch.object(RationalRadialTwist, "forward", side_effect=AssertionError("unneeded twist")):
            sampled_rational_coverage(cell(1), 0, first.with_twist(twist), second.with_twist(twist))
        with self.assertRaises(ValueError):
            sampled_rational_coverage(cell(1), 0, first, second, mode="approximate")


class RationalPressureTests(unittest.TestCase):
    def test_complete_pressure_report_matches_reference_with_compilation(self):
        identity = RationalLayerMap()
        shifted = RationalLayerMap(RationalAffine.similarity("5/4", "1/9", origin=("1/7", "-2/11")))
        args = ({cell(0): 3, cell(0, 1, -1): 2}, {cell(1): 4, cell(1, 2, -1): 3})
        kwargs = dict(upper_layer=0, before_upper_map=identity, before_lower_map=shifted,
                      after_lower_map=shifted.reanchor(("2/3", "-5/7")), inventory_complete=True)
        self.assertEqual(compare_rational_pressure(*args, **kwargs, mode="auto"),
                         compare_rational_pressure(*args, **kwargs, mode="reference"))

    def test_q16_projection_can_change_final_display_so_it_is_not_an_input(self):
        support = Fraction(64, 96)
        exact_score = rational_pressure_score(1, support)
        q16_support = normalize_q16_weights([64, 32])[0]
        self.assertEqual(exact_score, Fraction(35, 2))
        self.assertEqual(pressure_display(exact_score), 18)
        self.assertEqual(q16_support, 43691)
        self.assertEqual(pressure_score(1, q16_support), 17)

    def test_exact_score_and_half_up_display_are_separate(self):
        self.assertEqual(rational_pressure_score(1, Fraction(1, 3)), 34)
        self.assertEqual(rational_pressure_score(1, 0), Fraction(101, 2))
        self.assertEqual(pressure_display(rational_pressure_score(1, 0)), 51)
        for demand in range(10):
            scores = [rational_pressure_score(demand, Fraction(n, 3)) for n in range(31)]
            self.assertEqual(scores, sorted(scores, reverse=True))
            self.assertTrue(all(1 <= pressure_display(score) <= 100 for score in scores))
        for support in range(10):
            scores = [rational_pressure_score(Fraction(n, 3), support) for n in range(31)]
            self.assertEqual(scores, sorted(scores))
        for args in ((-1, 0, 1), (1, -1, 1), (1, 0, 0)):
            with self.assertRaises(ValueError):
                rational_pressure_score(*args)
        with self.assertRaises(TypeError):
            rational_pressure_score(1, 0.1)

    def test_current_material_is_conserved_with_exact_sample_support(self):
        identity = RationalLayerMap()
        shifted = RationalLayerMap(RationalAffine(origin=("1/7", "1/11")))
        upper, lower = {cell(0): 4}, {cell(1): 3, cell(1, 2, -1): 2}
        report = evaluate_rational_pressure(upper, lower, upper_layer=0, upper_map=identity,
                                           lower_map=shifted, inventory_complete=True)
        self.assertEqual(rational_from_mapping(report["distributed_support"]), 5)
        for source, units in lower.items():
            entries = [a for a in report["allocations"] if GeometryAddress.from_mapping(a["source"]) == source]
            self.assertEqual(sum(rational_from_mapping(a["weight"]) for a in entries), 1)
            self.assertEqual(sum(rational_from_mapping(a["support"]) for a in entries), units)
        at_origin = by_cell(report)[cell(0)]
        support = rational_from_mapping(at_origin["support"])
        self.assertEqual(rational_from_mapping(at_origin["pressure_exact"]),
                         1 + 99 * max(4 - support, 0) / 5)
        second = evaluate_rational_pressure(upper, {}, upper_layer=0, upper_map=identity,
                                           lower_map=shifted, inventory_complete=True)
        self.assertEqual(rational_from_mapping(second["distributed_support"]), 0)
        self.assertEqual(json.loads(json.dumps(report)), report)

    def test_comparison_keeps_union_and_exact_deficit_delta(self):
        identity = RationalLayerMap()
        shifted = RationalLayerMap(RationalAffine(origin=(4, 0)))
        upper, lower = {cell(0): 4}, {cell(1): 4}
        report = compare_rational_pressure(upper, lower, upper_layer=0,
                    before_upper_map=identity, before_lower_map=identity,
                    after_lower_map=shifted, inventory_complete=True)
        self.assertEqual(report["before"]["evaluation_region"], report["after"]["evaluation_region"])
        self.assertIn(cell(0), by_cell(report["after"]))
        self.assertIn(cell(0, 4, 0), by_cell(report["before"]))
        self.assertEqual(rational_from_mapping(report["before"]["total_deficit"]), 0)
        self.assertEqual(rational_from_mapping(report["after"]["total_deficit"]), 4)
        self.assertEqual(rational_from_mapping(report["delta"]["total_deficit"]), 4)
        self.assertEqual(sum(rational_from_mapping(c["delta_support"]) for c in report["coverage_changes"]), 0)
        self.assertTrue(report["advisory"])

    def test_partial_inventory_preserves_unknown_demand_and_deficit(self):
        identity = RationalLayerMap()
        shifted = RationalLayerMap(RationalAffine(origin=("1/2", 0)))
        report = compare_rational_pressure({cell(0): 5}, {cell(1): 2}, upper_layer=0,
                    before_upper_map=identity, before_lower_map=identity, after_lower_map=shifted)
        self.assertIsNone(report["delta"]["total_deficit"])
        for side in (report["before"], report["after"]):
            self.assertIsNone(side["total_deficit"])
            self.assertEqual(by_cell(side)[cell(0)]["score_kind"], "upper_estimate")
            unknown = [x for x in side["cells"] if x["demand_units"] is None]
            self.assertTrue(unknown)
            self.assertTrue(all(x["pressure"] is None and x["pressure_exact"] is None for x in unknown))

    def test_inventory_domain_and_counts_are_checked_once(self):
        identity = RationalLayerMap()
        for upper, lower, layer in (({cell(0): -1}, {}, 0), ({}, {cell(2): 1}, 0), ({}, {}, 64)):
            with self.assertRaises(ValueError):
                evaluate_rational_pressure(upper, lower, upper_layer=layer,
                                          upper_map=identity, lower_map=identity)


if __name__ == "__main__":
    unittest.main()
