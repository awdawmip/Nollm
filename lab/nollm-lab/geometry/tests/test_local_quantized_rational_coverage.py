"""Public local p8 input/output contracts and actual JSON command execution."""
from dataclasses import replace
from fractions import Fraction as F
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from nollm_core import GeometryAddress
from geometry.local_p8_cli import evaluate_request
from geometry.rational_coverage import (
    compare_rational_pressure, evaluate_rational_pressure, sampled_rational_coverage,
)
from geometry.rational_geometry import (
    RationalAffine, RationalLayerMap, RationalRadialTwist, rational_from_mapping,
)


CLI = Path(__file__).resolve().parents[1] / "local_p8_cli.py"


def cell(layer, q=0, r=0):
    return GeometryAddress("default_dream_v1", "default", layer, q, r)


def maps():
    lower = RationalLayerMap(RationalAffine.similarity("5/4", "1/7"),
                             (RationalRadialTwist(("1/9", "-2/7"), 9, "1/5"),))
    upper = RationalLayerMap(RationalAffine.similarity("7/6", "-1/11", origin=("1/17", "-2/19")))
    return upper, lower


def world_scale(mapping, factor):
    frame = replace(mapping.frame,
                    matrix=tuple(tuple(factor*x for x in row) for row in mapping.frame.matrix),
                    origin=tuple(factor*x for x in mapping.frame.origin))
    twists = tuple(replace(twist, center=tuple(factor*x for x in twist.center),
                           radius_squared=factor*factor*twist.radius_squared)
                   for twist in mapping.twists)
    return RationalLayerMap(frame, twists)


def pressure_request():
    upper, lower = maps()
    return {
        "operation": "pressure", "upper_layer": 0,
        "upper_map": upper.to_mapping(), "lower_map": lower.to_mapping(),
        "upper_units": [{"cell": cell(0).to_mapping(), "units": 7}],
        "lower_units": [{"cell": cell(1).to_mapping(), "units": 10**60+7},
                        {"cell": cell(1, 1, -1).to_mapping(), "units": 11}],
        "local_length": "5/4", "inventory_complete": True,
    }


def coverage_request():
    upper, lower = maps()
    return {"operation": "coverage", "source": cell(1).to_mapping(), "target_layer": 0,
            "source_map": lower.to_mapping(), "target_map": upper.to_mapping(),
            "local_length": "5/4"}


class LocalQuantizedCoverageTests(unittest.TestCase):
    def test_only_adjacent_admitted_layers_are_evaluated(self):
        upper, lower = maps()
        for target_layer in (1, 3, -64, 65):
            with self.subTest(target_layer=target_layer), self.assertRaisesRegex(ValueError, "adjacent"):
                sampled_rational_coverage(cell(1), target_layer, lower, upper,
                                           mode="local_quantized", local_length="5/4")
        for target_layer in (0, 2):
            coverage = sampled_rational_coverage(cell(1), target_layer, lower, upper,
                                                 mode="local_quantized", local_length="5/4")
            self.assertEqual(sum(m.hit_count for m in coverage.members), 96)
            self.assertEqual(sum(m.weight for m in coverage.members), 1)
            self.assertEqual(sum(m.weight_q16 for m in coverage.members), 65536)
            self.assertTrue(all(m.target.layer == target_layer for m in coverage.members))

    def test_large_material_inventory_conserves_exact_support(self):
        result = evaluate_request(pressure_request())
        expected = 10**60 + 18
        self.assertEqual(result["supplied_lower_units"], expected)
        self.assertEqual(rational_from_mapping(result["distributed_support"]), expected)
        self.assertEqual(sum(rational_from_mapping(a["support"]) for a in result["allocations"]), expected)
        self.assertEqual(sum(rational_from_mapping(c["support"]) for c in result["cells"]), expected)
        self.assertEqual(result["fractional_bits"], 8)
        self.assertEqual(rational_from_mapping(result["local_length"]), F(5, 4))

    def test_partial_inventory_preserves_unknown_demand(self):
        upper, lower = maps()
        unknown = cell(0, 20, 20)
        result = evaluate_rational_pressure({cell(0): 7}, {cell(1): 3}, upper_layer=0,
            upper_map=upper, lower_map=lower, evaluation_cells=(unknown,),
            mode="local_quantized", local_length="5/4")
        self.assertIsNone(result["total_deficit"])
        row = next(row for row in result["cells"] if row["cell"] == unknown.to_mapping())
        self.assertIsNone(row["demand_units"])
        self.assertIsNone(row["pressure"])
        self.assertIsNone(row["write_weight"])
        self.assertEqual(row["score_kind"], "demand_unknown")
        known = next(row for row in result["cells"] if row["cell"] == cell(0).to_mapping())
        self.assertEqual(known["score_kind"], "upper_estimate")
        self.assertFalse(known["support_complete"])

    def test_empty_inventory_still_requires_a_declared_unit(self):
        upper, lower = maps()
        with self.assertRaisesRegex(ValueError, "local_length"):
            evaluate_rational_pressure({}, {}, upper_layer=0, upper_map=upper,
                                       lower_map=lower, mode="local_quantized")
        result = evaluate_rational_pressure({}, {}, upper_layer=0, upper_map=upper,
            lower_map=lower, mode="local_quantized", local_length="5/4", inventory_complete=True)
        self.assertEqual(result["allocations"], [])
        self.assertEqual(rational_from_mapping(result["distributed_support"]), 0)
        self.assertEqual(rational_from_mapping(result["total_deficit"]), 0)

    def test_comparison_uses_each_world_unit_without_changing_pressure(self):
        upper, lower = maps()
        factor = F(3, 17)
        result = compare_rational_pressure({cell(0): 7}, {cell(1): 9, cell(1, 1, -1): 3},
            upper_layer=0, before_upper_map=upper, before_lower_map=lower,
            after_upper_map=world_scale(upper, factor), after_lower_map=world_scale(lower, factor),
            mode="local_quantized", local_length="5/4", after_local_length=F(5, 4)*factor,
            inventory_complete=True)
        self.assertEqual(result["coverage_changes"], [])
        self.assertEqual(result["before"]["allocations"], result["after"]["allocations"])
        self.assertEqual(result["before"]["cells"], result["after"]["cells"])
        self.assertEqual(rational_from_mapping(result["delta"]["total_deficit"]), 0)
        self.assertEqual(result["delta"]["max_known_pressure"], 0)
        self.assertEqual(rational_from_mapping(result["before"]["local_length"]), F(5, 4))
        self.assertEqual(rational_from_mapping(result["after"]["local_length"]), F(15, 68))

    def test_inventory_layer_mismatch_is_explicit(self):
        upper, lower = maps()
        with self.assertRaisesRegex(ValueError, "selected default axial layer"):
            evaluate_rational_pressure({cell(1): 3}, {cell(1): 2}, upper_layer=0,
                upper_map=upper, lower_map=lower, mode="local_quantized", local_length="5/4")


class LocalP8CommandTests(unittest.TestCase):
    def invoke(self, request, *, use_stdin=False):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "request.json"
            path.write_text(json.dumps(request), encoding="utf-8")
            return subprocess.run([sys.executable, str(CLI), "--input", "-" if use_stdin else str(path)],
                                  input=json.dumps(request) if use_stdin else None,
                                  cwd=tmp, text=True, capture_output=True, check=False)

    def test_coverage_command_runs_outside_repository_and_returns_full_result(self):
        request = coverage_request()
        result = self.invoke(request)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), evaluate_request(request))
        self.assertEqual(json.loads(result.stdout)["fractional_bits"], 8)

    def test_pressure_command_accepts_stdin_and_keeps_large_counts(self):
        request = pressure_request()
        result = self.invoke(request, use_stdin=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), evaluate_request(request))

    def test_command_reports_missing_unit_without_a_traceback(self):
        request = coverage_request()
        request.pop("local_length")
        result = self.invoke(request)
        self.assertEqual(result.returncode, 2)
        self.assertIn("local_length is required", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_command_reports_duplicate_cells_instead_of_overwriting_units(self):
        request = pressure_request()
        request["lower_units"].append(request["lower_units"][0])
        result = self.invoke(request)
        self.assertEqual(result.returncode, 2)
        self.assertIn("duplicate cell", result.stderr)

    def test_command_keeps_explicit_precision_and_rejects_ambiguous_count_types(self):
        request = coverage_request()
        request["fractional_bits"] = 12
        result = self.invoke(request)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["fractional_bits"], 12)
        for value in ("3", 1.5, True):
            request = pressure_request()
            request["lower_units"][0]["units"] = value
            with self.subTest(value=value), self.assertRaisesRegex(TypeError, "units must be integers"):
                evaluate_request(request)


if __name__ == "__main__":
    unittest.main()
