from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

from subprocess_harness import run_subprocess, subprocess_failure_message

from nollm.dream_regression import (
    build_dream_regression_report,
    default_dream_regression_cases,
    validate_dream_regression_report,
)


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "reference" / "python" / "scripts" / "run_dream_regression_pack.py"


class DreamRegressionTests(unittest.TestCase):
    def test_report_status_is_experimental_candidate(self) -> None:
        report = build_dream_regression_report()
        self.assertEqual(report["status"], "experimental_candidate")

    def test_all_default_regression_cases_pass_expectations(self) -> None:
        report = build_dream_regression_report()
        self.assertTrue(report["summary"]["ok"])
        self.assertTrue(all(case["ok"] for case in report["cases"]))

    def test_report_validates_and_is_json_primitive(self) -> None:
        report = build_dream_regression_report()
        validate_dream_regression_report(report)
        json.dumps(report, sort_keys=True)

    def test_report_is_deterministic_when_case_order_is_reversed(self) -> None:
        cases = default_dream_regression_cases()
        first = build_dream_regression_report(cases)
        second = build_dream_regression_report(tuple(reversed(cases)))
        self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))

    def test_validator_rejects_forbidden_field_in_final_report(self) -> None:
        report = build_dream_regression_report()
        report["parent_id"] = "bad"
        with self.assertRaises(ValueError):
            validate_dream_regression_report(report)

    def test_malformed_shard_case_fails_correctly(self) -> None:
        report = build_dream_regression_report()
        case = _case_by_id(report, "missing_shard_id")
        self.assertEqual(case["observed"], "fail")
        self.assertTrue(case["ok"])

    def test_malformed_placement_energy_case_fails_correctly(self) -> None:
        report = build_dream_regression_report()
        case = _case_by_id(report, "non_numeric_energy_term")
        self.assertEqual(case["observed"], "fail")
        self.assertTrue(case["ok"])

    def test_script_writes_deterministic_json_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "regression_report.json"
            result = run_subprocess(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
                timeout_seconds=20,
            )
            self.assertEqual(
                result.returncode,
                0,
                subprocess_failure_message(result, ROOT, "run_dream_regression_pack"),
            )
            first = output.read_text(encoding="utf-8")
            result = run_subprocess(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
                timeout_seconds=20,
            )
            self.assertEqual(result.returncode, 0)
            self.assertEqual(first, output.read_text(encoding="utf-8"))
            self.assertIn("wrote dream regression report", result.stdout)


def _case_by_id(report: dict[str, object], case_id: str) -> dict[str, object]:
    for case in report["cases"]:
        if case["case_id"] == case_id:
            return case
    raise AssertionError(f"missing case {case_id}")


if __name__ == "__main__":
    unittest.main()
