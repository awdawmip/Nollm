"""The lossy fixed-point contract accepts its labels without exact repair."""
from dataclasses import replace
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from nollm_core import GeometryAddress
from geometry.quantized_rational_kernel import compile_quantized_pair
from geometry.rational_geometry import (
    RationalAffine, RationalLayerMap, RationalRadialTwist, relative_layer_maps, rational_from_mapping,
)
from geometry.rational_coverage import (
    evaluate_rational_pressure, rational_sample_numerators, sampled_rational_coverage,
)
from geometry.benchmark_quantized_rational import (
    build_scenarios, compiler, complete_coverage_run, prepare_case, pressure_values,
    structural_metrics, world_shift,
)


def fraction_schedule(source, target, point, bits):
    """Independent Fraction implementation of the declared rounded recurrence."""
    source, target = relative_layer_maps(source, target)
    scale = 1 << bits
    rnd = lambda value: F(round(value*scale), scale)
    point = tuple(rnd(value) for value in source.frame.forward(point))
    for sequence, sign in ((source.twists, 1), (reversed(target.twists), -1)):
        for twist in sequence:
            center = tuple(rnd(value) for value in twist.center)
            u, v = (a-b for a, b in zip(point, center))
            radius = rnd(u*u+u*v+v*v)
            cutoff = max(F(0), 1-rnd(radius/twist.radius_squared))
            t = rnd(rnd(cutoff*cutoff)*sign*twist.strength)
            if t == 0:
                continue
            t2 = rnd(t*t)
            divisor, middle = 1+3*t2, 1-3*t2
            point = (center[0]+rnd(((middle-2*t)*u-4*t*v)/divisor),
                     center[1]+rnd((4*t*u+(middle+2*t)*v)/divisor))
    return tuple(rnd(value) for value in target.frame.inverse(point))


def pair():
    source = RationalLayerMap(RationalAffine.similarity("5/4", "1/7", origin=("2/11", "-1/13")),
        (RationalRadialTwist(("1/9", "-2/7"), 9, "1/5"),
         RationalRadialTwist(("-1/5", "1/11"), 4, "-1/7")))
    target = RationalLayerMap(RationalAffine.similarity("7/6", "-1/11", origin=("1/17", "-2/19")),
        (RationalRadialTwist(("-2/13", "1/7"), 6, "1/9"),))
    return source, target


class QuantizedRationalTests(unittest.TestCase):
    def test_integer_kernel_matches_independent_rounded_fraction_schedule(self):
        source, target = pair()
        for bits in (0, 3, 8, 16):
            kernel = compile_quantized_pair(source, target, fractional_bits=bits)
            for q, r in ((0, 0), (1, -2), (-11, 7), (19, 23), (36, -36)):
                qn, rn, denominator = kernel.map_ratio(q, r, 36)
                self.assertEqual(denominator, 1 << bits)
                self.assertEqual((F(qn, denominator), F(rn, denominator)),
                                 fraction_schedule(source, target, (F(q, 36), F(r, 36)), bits))

    def test_precision_errors_are_returned_without_adaptive_or_exact_repair(self):
        scenario = next(s for s in build_scenarios(20261123) if s.name == "one_hit_delta_2_pow_minus_40")
        expected = sampled_rational_coverage(GeometryAddress("default_dream_v1", "default", 1, 0, 0),
                                              0, scenario.lower, scenario.upper, mode="reference")
        self.assertEqual({(m.target.q, m.target.r): m.hit_count for m in expected.members},
                         {(0, 0): 95, (1, 0): 1})
        with patch.object(RationalLayerMap, "forward", side_effect=AssertionError("exact mapping")), \
             patch.object(RationalLayerMap, "inverse", side_effect=AssertionError("exact inverse")), \
             patch("geometry.rational_coverage.compile_adaptive_pair", side_effect=AssertionError("adaptive repair")):
            actual = sampled_rational_coverage(GeometryAddress("default_dream_v1", "default", 1, 0, 0),
                0, scenario.lower, scenario.upper, mode="quantized", fractional_bits=16)
        self.assertEqual({(m.target.q, m.target.r): m.hit_count for m in actual.members}, {(0, 0): 96})
        self.assertEqual(actual.contract_id, "lab_quantized_rational_axial_quadrature_v1")
        self.assertEqual(actual.to_mapping()["share_basis"], "quantized_sample_share")
        self.assertEqual(actual.to_mapping()["fractional_bits"], 16)
        self.assertNotIn("fractional_bits", expected.to_mapping())
        default_precision = sampled_rational_coverage(
            GeometryAddress("default_dream_v1", "default", 1, 0, 0),
            0, scenario.lower, scenario.upper, mode="quantized")
        self.assertEqual(default_precision.to_mapping()["fractional_bits"], 12)

    def test_affine_path_retains_exact_inexpensive_integer_calculation(self):
        source = RationalLayerMap(RationalAffine(origin=(F(1, 2)+F(1, 1 << 80), 0)))
        kernel = compile_quantized_pair(source, RationalLayerMap(), fractional_bits=0)
        self.assertEqual(kernel.execution_kind, "integer_affine")
        self.assertEqual(kernel.targets(0, 0, ((0, 0),), 1), ((1, 0),))

    def test_common_world_anchor_and_representation_reanchor_are_invariant(self):
        source, target = pair()
        expected = compile_quantized_pair(source, target, fractional_bits=8).targets(
            1, -1, rational_sample_numerators(), 36)
        variants = ((world_shift(source, (2**160, -2**160)), world_shift(target, (2**160, -2**160))),
                    (source.reanchor(("13/17", "-19/23")), target.reanchor(("-7/11", "29/31"))))
        for first, second in variants:
            self.assertEqual(compile_quantized_pair(first, second, fractional_bits=8).targets(
                1, -1, rational_sample_numerators(), 36), expected)

    def test_common_suffix_cancelled_before_lossy_execution(self):
        source, target = pair()
        twist = RationalRadialTwist(("-3/11", "2/13"), 7, "3/8")
        direct = compile_quantized_pair(source, target, fractional_bits=6)
        cancelled = compile_quantized_pair(source.with_twist(twist), target.with_twist(twist), fractional_bits=6)
        self.assertEqual(cancelled.cancelled_common_twists, 1)
        self.assertEqual(cancelled.targets(0, 0, rational_sample_numerators(), 36),
                         direct.targets(0, 0, rational_sample_numerators(), 36))


class QuantizedBenchmarkTests(unittest.TestCase):
    def test_frozen_inventory_has_declared_strata_and_separate_stress(self):
        first, second = build_scenarios(20261123), build_scenarios(20261124)
        main = [s for s in first if s.cohort == "main"]
        self.assertEqual(len(main), 24)
        self.assertTrue(all(len(s.coordinates) == 8 and len(set(s.coordinates)) == 8 for s in main))
        self.assertEqual({s.depth for s in main}, {1, 2, 3, 5})
        self.assertEqual({s.direction for s in main}, {"up", "down"})
        self.assertEqual(len([s for s in first if s.cohort == "stress"]), 2)
        self.assertEqual([s.mapping() for s in first], [s.mapping() for s in build_scenarios(20261123)])
        self.assertNotEqual([s.mapping() for s in first], [s.mapping() for s in second])

    def test_structure_metrics_use_edge_denominators_and_lost_mass(self):
        reference = (((0, 0),)*95+((1, 0),),)
        candidate = (((0, 0),)*96,)
        result = structural_metrics(reference, candidate)
        self.assertEqual(result["fn_over_reference_edges"], .5)
        self.assertEqual(result["structural_error_micro"], .5)
        self.assertEqual(result["fp_over_candidate_edges"], 0)
        self.assertEqual(result["label_mismatch_rate"], 1/96)
        self.assertEqual(result["mean_tv"], 1/96)
        self.assertEqual(result["lost_edge_mass_mean"], 1/96)
        changed = structural_metrics(reference, (((0, 0),)*95+((2, 0),),))
        self.assertEqual(changed["structural_error_micro"], 2/3)
        self.assertEqual(changed["fp_over_candidate_edges"], .5)
        self.assertEqual(changed["fp_over_reference_edges"], .5)

    def test_compiled_reuse_times_the_same_complete_coverage_outputs(self):
        scenario = replace(build_scenarios(20261123)[0], coordinates=((0, 0),))
        for mode in ("q8", "adaptive16"):
            direct = complete_coverage_run(scenario, mode)
            reused = complete_coverage_run(scenario, mode, compiler(*scenario.pair(), mode))
            self.assertEqual(direct, reused)

    def test_pressure_metric_arithmetic_agrees_with_public_complete_inventory_api(self):
        scenario = replace(build_scenarios(20261123)[0], coordinates=((0, 0),))
        record = prepare_case(scenario, 20261123, 0)
        data = record["pressure"]
        lower = {GeometryAddress("default_dream_v1", "default", 1, q, r): n
                 for (q, r), n in zip(scenario.coordinates, data["lower_units"])}
        upper = {GeometryAddress("default_dream_v1", "default", 0, q, r): n for q, r, n in data["upper_units"]}
        labels = compile_quantized_pair(scenario.lower, scenario.upper, fractional_bits=4).targets(
            0, 0, rational_sample_numerators(), 36)
        demands = {(c.q, c.r): n for c, n in upper.items()}
        region = set(demands) | set(labels)
        exact, display, deficit = pressure_values((labels,), data["lower_units"], demands, region)
        actual = evaluate_rational_pressure(upper, lower, upper_layer=0, lower_map=scenario.lower,
            upper_map=scenario.upper, inventory_complete=True, mode="quantized", fractional_bits=4)
        self.assertEqual(rational_from_mapping(actual["total_deficit"]), deficit)
        for item in actual["cells"]:
            key = item["cell"]["q"], item["cell"]["r"]
            self.assertEqual(item["pressure"], display[key])
            self.assertEqual(rational_from_mapping(item["pressure_exact"]), exact[key])


if __name__ == "__main__":
    unittest.main()
