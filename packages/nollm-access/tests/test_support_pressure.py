"""Behavioral pressure checks with canonical physical identities and real coverage."""
from fractions import Fraction
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from nollm_access.support_pressure import pressure_score, write_pressure
from nollm_core import (
    CoreRuntime,
    GeometryAddress,
    MemoryAtom,
    Q16_ONE,
    expand_physical_coverage,
    incoming_coverage,
)


def cell(layer=0, q=0, r=0):
    return GeometryAddress("default_dream_v1", "default", layer, q, r)


class SupportPressureTests(unittest.TestCase):
    def test_review_examples_and_half_up_rounding(self):
        for demand, support, expected in ((0, 0, 1), (1, 0, 51), (2, 0, 67),
                                           (4, 0, 80), (8, 0, 89), (8, 1, 78),
                                           (8, 4, 45), (8, 8, 1), (8, 16, 1),
                                           (9, 8, 11), (16, 8, 48)):
            with self.subTest(demand=demand, support=support):
                self.assertEqual(pressure_score(demand, support * Q16_ONE), expected)

    def test_score_matches_fraction_definition_and_monotonicity(self):
        for demand in range(21):
            for support_q16 in range(0, 21 * Q16_ONE, Q16_ONE // 4):
                support = Fraction(support_q16, Q16_ONE)
                value = 1 + 99 * max(demand - support, 0) / Fraction(demand + 1)
                rounded = (2 * value.numerator + value.denominator) // (2 * value.denominator)
                score = pressure_score(demand, support_q16)
                self.assertEqual(score, rounded)
                self.assertLessEqual(score, pressure_score(demand + 1, support_q16))
                self.assertGreaterEqual(score, pressure_score(demand, support_q16 + Q16_ONE // 4))
        self.assertEqual(pressure_score(10**12, 0), 100)

    def test_invalid_count_or_scale_is_not_a_numeric_score(self):
        for demand, support, kappa in ((-1, 0, 1), (1, -1, 1), (1, 0, 0), (1, 0, -1)):
            with self.assertRaises(ValueError):
                pressure_score(demand, support, kappa)
        with self.assertRaises(ValueError):
            write_pressure(cell(), lambda _: (), additions=-1)

    def test_source_material_is_conserved_and_observations_are_not_material(self):
        source = cell(1, -7, 5)
        direct = expand_physical_coverage(source, "coverage_up")
        def units_at(address):
            return ("canonical-unit",) * 20 if address == source else ()
        reports = [write_pressure(m.target, units_at, additions=0) for m in direct.members]
        self.assertEqual([r.support_q16 for r in reports], [m.weight_q16 for m in direct.members])
        self.assertEqual(sum(r.support_q16 for r in reports), Q16_ONE)
        self.assertEqual(reports[0].support_q16, 1365)
        self.assertTrue(all(r.support_complete for r in reports))

    def test_incoming_witness_supplies_support_even_when_down_misses_it(self):
        parent, child = cell(0, 67, 5), cell(1, 94, -30)
        units = {parent: ("upper",), child: ("lower",)}
        report = write_pressure(parent, lambda address: units.get(address, ()), additions=0)
        self.assertEqual(report.support_q16, 683)
        self.assertTrue(report.support_complete)

    def test_unknown_lower_material_gives_an_upper_estimate(self):
        parent = cell()
        source = incoming_coverage(parent).members[0].source
        units = {parent: tuple(range(8)), source: ("a", "b", "c", "d")}
        full = write_pressure(parent, lambda address: units.get(address, ()), additions=0)
        partial = write_pressure(parent, lambda address: None if address == source else units.get(address, ()),
                                 additions=0)
        self.assertFalse(partial.support_complete)
        self.assertIn(source, partial.unknown_cells)
        self.assertEqual(partial.score_kind, "upper_estimate")
        self.assertGreaterEqual(partial.pressure, full.pressure)

    def test_unknown_demand_has_no_score(self):
        parent = cell()
        result = write_pressure(parent, lambda address: None if address == parent else ())
        self.assertIsNone(result.demand_units)
        self.assertIsNone(result.pressure)
        self.assertIsNone(result.write_weight)
        self.assertFalse(result.demand_complete)
        self.assertEqual(result.to_mapping()["score_kind"], "demand_unknown")

    def test_bottom_domain_is_reported_as_unavailable_support(self):
        result = write_pressure(cell(64), lambda _: ())
        self.assertEqual(result.pressure, 51)
        self.assertFalse(result.support_complete)
        self.assertTrue(result.geometry_error)

    def test_empty_candidates_are_compared_after_the_same_write(self):
        reports = [write_pressure(cell(layer), lambda _: ()) for layer in (0, 1, 2, 3)]
        self.assertEqual([r.pressure for r in reports], [51] * 4)
        self.assertEqual([r.write_weight for r in reports], [50] * 4)

    def test_current_handles_survive_repeated_reads_and_revision(self):
        with TemporaryDirectory() as temporary, CoreRuntime(Path(temporary)) as core:
            parent = cell()
            source = incoming_coverage(parent).members[0].source
            upper = core.put(MemoryAtom("upper", "Upper understanding."), parent)
            lower = core.put(MemoryAtom("lower", "Lower material."), source)
            def units_at(address):
                return [handle for handle, _ in core.atoms_at(address)]
            before = core.export_state_bytes()
            result = write_pressure(parent, units_at, additions=0)
            for _ in range(5):
                self.assertEqual(write_pressure(parent, units_at, additions=0), result)
            self.assertEqual(before, core.export_state_bytes())
            core.replace(lower, "Revised lower material, same physical unit.")
            revised = write_pressure(parent, units_at, additions=0)
            self.assertEqual(revised.support_q16, result.support_q16)
            self.assertEqual(revised.pressure, result.pressure)
            self.assertEqual(write_pressure(parent, units_at).demand_units, 2)
            self.assertEqual(core.get(upper).payload_utf8, "Upper understanding.")


if __name__ == "__main__":
    unittest.main()
