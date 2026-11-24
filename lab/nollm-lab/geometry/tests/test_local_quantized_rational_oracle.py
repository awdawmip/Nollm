"""Independent scalar checks for the source-cell local quantized contract.

The oracle uses Fraction affine evaluation, Python's Fraction half-even round,
and an explicit recurrence. It does not call the candidate's normalization,
integer affine kernel, fixed-point twist, or axial classifier.
"""
from collections import Counter, defaultdict
from dataclasses import replace
from fractions import Fraction as F
import unittest

from geometry.local_quantized_rational_kernel import compile_local_quantized_pair
from nollm_core import GeometryAddress
from geometry.rational_coverage import (
    compare_rational_pressure, evaluate_rational_pressure, rational_sample_numerators,
    sampled_rational_coverage,
)
from geometry.rational_geometry import RationalAffine, RationalLayerMap, RationalRadialTwist


def nearest_fraction(q, r):
    """Independent absolute-coordinate half-even cube classification."""
    iq, ir, iy = round(q), round(r), round(-q-r)
    errors = abs(iq-q), abs(ir-r), abs(iy+q+r)
    if errors[0] >= errors[1] and errors[0] >= errors[2]:
        iq = -iy-ir
    elif errors[1] >= errors[2]:
        ir = -iq-iy
    return iq, ir


def fraction_schedule(source, target, cell, offset, unit, bits):
    """The declared local schedule, evaluated with scalar rational arithmetic."""
    source_twists = [twist for twist in source.twists if twist.strength]
    target_twists = [twist for twist in target.twists if twist.strength]
    while source_twists and target_twists and source_twists[-1] == target_twists[-1]:
        source_twists.pop()
        target_twists.pop()
    absolute_point = tuple(F(c)+u for c, u in zip(cell, offset))
    if not source_twists and not target_twists:
        return target.frame.inverse(source.frame.forward(absolute_point))

    scale = 1 << bits
    rounded = lambda value: F(round(value*scale), scale)
    origin = source.frame.forward(cell)
    point = tuple(rounded((x-o)/unit)
                  for x, o in zip(source.frame.forward(absolute_point), origin))
    for twists, sign in ((source_twists, 1), (reversed(target_twists), -1)):
        for twist in twists:
            center = tuple(rounded((x-o)/unit) for x, o in zip(twist.center, origin))
            radius_squared = twist.radius_squared/(unit*unit)
            u, v = (x-c for x, c in zip(point, center))
            norm = rounded(u*u+u*v+v*v)
            cutoff = max(F(0), 1-rounded(norm/radius_squared))
            parameter = rounded(rounded(cutoff*cutoff)*sign*twist.strength)
            if not parameter:
                continue
            squared = rounded(parameter*parameter)
            divisor, middle = 1+3*squared, 1-3*squared
            point = (center[0]+rounded(((middle-2*parameter)*u-4*parameter*v)/divisor),
                     center[1]+rounded((4*parameter*u+(middle+2*parameter)*v)/divisor))
    world = tuple(x*unit+o for x, o in zip(point, origin))
    return tuple(rounded(x) for x in target.frame.inverse(world))


def pair():
    source = RationalLayerMap(
        RationalAffine.similarity("5/4", "1/7", origin=("2/11", "-1/13")),
        (RationalRadialTwist(("1/9", "-2/7"), 9, "1/5"),
         RationalRadialTwist(("-1/5", "1/11"), 4, "-1/7")))
    target = RationalLayerMap(
        RationalAffine.similarity("7/6", "-1/11", origin=("1/17", "-2/19")),
        (RationalRadialTwist(("-2/13", "1/7"), 6, "1/9"),))
    return source, target


def world_similarity(mapping, multiplier, shift):
    """An exact change of world representation x -> multiplier*x + shift."""
    frame = replace(mapping.frame,
                    matrix=tuple(tuple(multiplier*x for x in row) for row in mapping.frame.matrix),
                    origin=tuple(multiplier*x+b for x, b in zip(mapping.frame.origin, shift)))
    twists = tuple(replace(twist,
                           center=tuple(multiplier*x+b for x, b in zip(twist.center, shift)),
                           radius_squared=multiplier*multiplier*twist.radius_squared)
                   for twist in mapping.twists)
    return RationalLayerMap(frame, twists)


def relabel_addresses(mapping, shift):
    """Keep physical positions while assigning local address x+shift to old x."""
    anchor = tuple(x+k for x, k in zip(mapping.frame.local_anchor, shift))
    return replace(mapping, frame=replace(mapping.frame, local_anchor=anchor))


def labels(kernel, cell):
    return kernel.targets(*cell, rational_sample_numerators(), 36)


class LocalQuantizedOracleTests(unittest.TestCase):
    def test_independent_fraction_schedule_all_samples_and_both_directions(self):
        source, target = pair()
        numerators = rational_sample_numerators()
        self.assertEqual(len(numerators), 96)
        for first, second in ((source, target), (target, source)):
            for bits in (0, 3, 8, 16):
                unit = F(5, 4)
                kernel = compile_local_quantized_pair(first, second,
                                                      local_length=unit, fractional_bits=bits)
                for cell in ((0, 0), (1, -2), (-3, 1)):
                    local = kernel.for_cell(*cell)
                    expected_labels = []
                    for dq, dr in numerators:
                        expected = fraction_schedule(first, second, cell,
                                                     (F(dq, 36), F(dr, 36)), unit, bits)
                        qn, rn, denominator = local.map_offset_ratio(dq, dr, 36)
                        self.assertEqual((F(qn, denominator), F(rn, denominator)), expected)
                        expected_labels.append(nearest_fraction(*expected))
                    self.assertEqual(labels(kernel, cell), tuple(expected_labels))

    def test_reanchor_source_target_and_both_preserves_every_label(self):
        source, target = pair()
        anchors = ((F(1, 3), F(1, 7)),
                   (F(2**130, 17), F(-2**127, 19)))
        cells = ((0, 0), (1, -2), (-3, 1))
        expected = tuple(labels(compile_local_quantized_pair(source, target, local_length="5/4"), c)
                         for c in cells)
        for anchor in anchors:
            for first, second in ((source.reanchor(anchor), target),
                                  (source, target.reanchor(anchor)),
                                  (source.reanchor(anchor), target.reanchor(anchor))):
                kernel = compile_local_quantized_pair(first, second, local_length="5/4")
                self.assertEqual(tuple(labels(kernel, c) for c in cells), expected)

    def test_declared_unit_preserves_full_shear_matrix(self):
        source, target = pair()
        source = replace(source, frame=RationalAffine(
            ((F(1), F(1, 7)), (F(-2, 9), F(7, 6))), origin=(F(1, 11), F(-2, 13))))
        unit, bits, cell = F(5, 4), 8, (1, -1)
        kernel = compile_local_quantized_pair(source, target, local_length=unit, fractional_bits=bits)
        expected = tuple(nearest_fraction(*fraction_schedule(source, target, cell,
                          (F(dq, 36), F(dr, 36)), unit, bits))
                         for dq, dr in rational_sample_numerators())
        self.assertEqual(labels(kernel, cell), expected)

    def test_declared_unit_follows_small_and_nonbinary_world_scales_and_huge_shifts(self):
        source, target = pair()
        cells = ((0, 0), (1, -2), (-3, 1))
        unit = F(5, 4)
        expected_kernel = compile_local_quantized_pair(source, target, local_length=unit)
        expected = tuple(labels(expected_kernel, c) for c in cells)
        transformations = (
            (F(1, 256), (F(0), F(0))),
            (F(1, 65536), (F(1, 3), F(-2, 7))),
            (F(3, 17), (F(2**160)+F(1, 3), F(-2**155)+F(2, 7))),
            (F(65536), (F(-2**100), F(2**103))),
        )
        for multiplier, shift in transformations:
            first, second = (world_similarity(m, multiplier, shift) for m in (source, target))
            kernel = compile_local_quantized_pair(first, second, local_length=unit*multiplier)
            self.assertEqual(tuple(labels(kernel, c) for c in cells), expected)
            first_local, second_local = expected_kernel.for_cell(1, -2), kernel.for_cell(1, -2)
            for dq, dr in ((1, 2), (-7, 3), (13, -11)):
                a, b, d = first_local.map_offset_ratio(dq, dr, 36)
                x, y, z = second_local.map_offset_ratio(dq, dr, 36)
                self.assertEqual((F(a, d), F(b, d)), (F(x, z), F(y, z)))

    def test_full_integer_source_and_target_addresses_remain_separate_from_fractional_bits(self):
        source, target = pair()
        cell = (1, -2)
        shift_source = (2**90+1, -2**88+3)
        shift_target = (2**120, -2**118)
        expected = labels(compile_local_quantized_pair(source, target, local_length="5/4"), cell)
        first = relabel_addresses(source, shift_source)
        second = relabel_addresses(target, shift_target)
        shifted_cell = tuple(c+k for c, k in zip(cell, shift_source))
        actual = labels(compile_local_quantized_pair(first, second, local_length="5/4"), shifted_cell)
        self.assertEqual(actual, tuple((q+shift_target[0], r+shift_target[1]) for q, r in expected))

    def test_large_address_is_multiplied_before_any_coordinate_rounding(self):
        source = RationalLayerMap(
            RationalAffine.similarity(F(1025, 1024)),
            (RationalRadialTwist((0, 0), 1, F(1, 16)),))
        kernel = compile_local_quantized_pair(source, RationalLayerMap(), local_length=F(1025, 1024))
        qn, rn, denominator = kernel.for_cell(2**29, 0).map_offset_ratio(0, 0, 1)
        self.assertEqual((F(qn, denominator), F(rn, denominator)), (F(537395200), F(0)))
        # Quantizing 1025/1024 to p8 first loses 524288 complete target cells.
        prematurely_rounded = F(round(F(1025, 1024)*256), 256)*2**29
        self.assertEqual(F(qn, denominator)-prematurely_rounded, 524288)

    def test_absolute_half_even_ties_preserve_odd_target_cell_parity(self):
        # An arbitrary integer anchor would misclassify 3/2 as 1 + round(1/2).
        self.assertEqual(nearest_fraction(F(1, 2), F(0)), (0, 0))
        self.assertEqual(nearest_fraction(F(3, 2), F(0)), (2, 0))
        for q, expected in ((F(1, 2), 0), (F(3, 2), 2),
                            (F(-1, 2), 0), (F(-3, 2), -2)):
            source = RationalLayerMap(
                RationalAffine(origin=(q, 0)),
                (RationalRadialTwist((50, 50), 1, F(1, 3)),))
            for bits in (0, 8):
                kernel = compile_local_quantized_pair(source, RationalLayerMap(),
                                                      local_length=1, fractional_bits=bits)
                self.assertEqual(kernel.targets(0, 0, ((0, 0),), 1), ((expected, 0),))

    def test_shared_outer_twists_cancel_before_local_rounding(self):
        source, target = pair()
        shared = (RationalRadialTwist(("5/13", "-3/17"), 7, "2/9"),
                  RationalRadialTwist(("-7/11", "2/19"), 11, "-3/8"))
        extended_source = replace(source, twists=(*source.twists, *shared))
        extended_target = replace(target, twists=(*target.twists, *shared))
        baseline = compile_local_quantized_pair(source, target, local_length="5/4")
        extended = compile_local_quantized_pair(extended_source, extended_target, local_length="5/4")
        for cell in ((0, 0), (1, -2), (-3, 1)):
            self.assertEqual(labels(extended, cell), labels(baseline, cell))

    def test_identity_twist_cannot_hide_a_shared_outer_suffix(self):
        source, target = pair()
        shared = RationalRadialTwist((0, 0), 9, "1/3")
        identity = RationalRadialTwist(("1/17", "3/19"), 7, 0)
        baseline = compile_local_quantized_pair(source, target, local_length="5/4")
        extended = compile_local_quantized_pair(source.with_twist(shared).with_twist(identity),
                                                target.with_twist(shared), local_length="5/4")
        # Before the compile-order correction, cell (1,1) changes samples 35,53,56.
        for cell in ((1, 1), (2, -1)):
            self.assertEqual(labels(extended, cell), labels(baseline, cell))

    def test_affine_only_path_keeps_exact_rational_boundary_offset(self):
        source = RationalLayerMap(RationalAffine(origin=(F(1, 2)+F(1, 1 << 80), 0)))
        kernel = compile_local_quantized_pair(source, RationalLayerMap(),
                                              local_length="1/65536", fractional_bits=0)
        qn, rn, denominator = kernel.for_cell(0, 0).map_offset_ratio(0, 0, 1)
        self.assertEqual((F(qn, denominator), F(rn, denominator)), source.frame.origin)
        self.assertEqual(kernel.targets(0, 0, ((0, 0),), 1), ((1, 0),))

    def test_local_length_is_explicit_positive_exact_input(self):
        source, target = pair()
        with self.assertRaises(TypeError):
            compile_local_quantized_pair(source, target)
        for invalid in (0, -1, "0", F(-1, 3)):
            with self.assertRaises(ValueError):
                compile_local_quantized_pair(source, target, local_length=invalid)
        with self.assertRaises(TypeError):
            compile_local_quantized_pair(source, target, local_length=1.0)

    def test_public_coverage_metadata_defaults_and_complete_hit_mass(self):
        source, target = pair()
        cell = GeometryAddress("default_dream_v1", "default", 1, 1, -2)
        coverage = sampled_rational_coverage(cell, 0, source, target,
                                             mode="local_quantized", local_length="5/4")
        expected = Counter(nearest_fraction(*fraction_schedule(source, target, (1, -2),
                           (F(dq, 36), F(dr, 36)), F(5, 4), 8))
                           for dq, dr in rational_sample_numerators())
        self.assertEqual({(m.target.q, m.target.r): m.hit_count for m in coverage.members}, expected)
        self.assertEqual(sum(m.hit_count for m in coverage.members), 96)
        self.assertEqual(sum(m.weight for m in coverage.members), 1)
        self.assertEqual(sum(m.weight_q16 for m in coverage.members), 65536)
        data = coverage.to_mapping()
        self.assertEqual(data["contract_id"], "lab_local_quantized_rational_axial_quadrature_v1")
        self.assertEqual(data["share_basis"], "local_quantized_sample_share")
        self.assertEqual(data["fractional_bits"], 8)
        self.assertEqual(data["local_length"], {"numerator": "5", "denominator": "4"})
        self.assertEqual(data["anchor_policy"], "source_cell_affine_center")
        self.assertEqual(data["target_anchor_policy"], "even_integer")
        with self.assertRaises(ValueError):
            sampled_rational_coverage(cell, 0, source, target, mode="local_quantized")
        old = sampled_rational_coverage(cell, 0, source, target, mode="quantized").to_mapping()
        self.assertEqual(old["fractional_bits"], 12)
        self.assertEqual(old["contract_id"], "lab_quantized_rational_axial_quadrature_v1")
        self.assertNotIn("local_length", old)
        exact = sampled_rational_coverage(cell, 0, RationalLayerMap(), RationalLayerMap()).to_mapping()
        self.assertEqual(exact["contract_id"], "lab_exact_rational_axial_quadrature_v1")
        self.assertNotIn("fractional_bits", exact)
        self.assertNotIn("local_length", exact)

    def test_pressure_matches_independent_counts_and_world_unit_change(self):
        source, target = pair()
        cell = lambda layer, q, r: GeometryAddress("default_dream_v1", "default", layer, q, r)
        lower = {cell(1, 0, 0): 7, cell(1, 1, -2): 11}
        upper = {cell(0, 0, 0): 11, cell(0, 1, -1): 9}
        support = defaultdict(F)
        for address, material in lower.items():
            for dq, dr in rational_sample_numerators():
                destination = nearest_fraction(*fraction_schedule(source, target,
                    (address.q, address.r), (F(dq, 36), F(dr, 36)), F(5, 4), 8))
                support[destination] += F(material, 96)
        result = evaluate_rational_pressure(upper, lower, upper_layer=0,
            upper_map=target, lower_map=source, inventory_complete=True,
            mode="local_quantized", local_length="5/4")
        to_fraction = lambda value: F(int(value["numerator"]), int(value["denominator"]))
        self.assertEqual(to_fraction(result["distributed_support"]), 18)
        for entry in result["cells"]:
            q, r = entry["cell"]["q"], entry["cell"]["r"]
            demand = upper.get(cell(0, q, r), 0)
            expected = 1+99*max(F(0), demand-support[q, r])/(demand+1)
            self.assertEqual(to_fraction(entry["support"]), support[q, r])
            self.assertEqual(to_fraction(entry["pressure_exact"]), expected)

        multiplier, shift = F(3, 17), (F(2**100)+F(1, 3), F(-2**100)+F(2, 7))
        comparison = compare_rational_pressure(upper, lower, upper_layer=0,
            before_upper_map=target, before_lower_map=source,
            after_upper_map=world_similarity(target, multiplier, shift),
            after_lower_map=world_similarity(source, multiplier, shift),
            inventory_complete=True, mode="local_quantized",
            local_length=F(5, 4), after_local_length=F(5, 4)*multiplier)
        self.assertEqual(comparison["coverage_changes"], [])
        self.assertEqual(comparison["before"]["cells"], comparison["after"]["cells"])
        self.assertEqual(to_fraction(comparison["before"]["local_length"]), F(5, 4))
        self.assertEqual(to_fraction(comparison["after"]["local_length"]), F(15, 68))
        self.assertEqual(to_fraction(comparison["delta"]["total_deficit"]), 0)


if __name__ == "__main__":
    unittest.main()
