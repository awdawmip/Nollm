from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

from subprocess_harness import run_subprocess, subprocess_failure_message

from nollm.dream_suite import (
    build_dream_geometry_suite_report,
    validate_dream_geometry_suite_report,
    write_dream_geometry_suite_report,
)


ROOT = Path(__file__).resolve().parents[3]
REFERENCE_PYTHON = ROOT / "reference" / "python"
SCRIPT = REFERENCE_PYTHON / "scripts" / "run_dream_geometry_suite.py"
FORBIDDEN_FIELDS = {
    "parent",
    "parent_id",
    "children",
    "child_ids",
    "belongs_to_anchor",
    "anchor_owner",
    "folder",
}


class DreamSuiteTests(unittest.TestCase):
    def test_report_is_json_serializable(self) -> None:
        report = build_dream_geometry_suite_report(ROOT)
        validate_dream_geometry_suite_report(report)
        json.dumps(report, sort_keys=True)

    def test_report_status_and_ok(self) -> None:
        report = build_dream_geometry_suite_report(ROOT)
        self.assertEqual(report["status"], "experimental_candidate")
        self.assertTrue(report["ok"])

    def test_components_are_present(self) -> None:
        report = build_dream_geometry_suite_report(ROOT)
        self.assertEqual(set(report["components"].keys()), {"pipeline", "batch", "regression"})
        self.assertGreater(report["components"]["batch"]["invariant_check_count"], 0)
        self.assertGreater(report["components"]["regression"]["case_count"], 0)

    def test_forbidden_semantics_flags_are_false(self) -> None:
        report = build_dream_geometry_suite_report(ROOT)
        self.assertEqual(
            report["forbidden_semantics"],
            {
                "parent_child": False,
                "anchor_ownership": False,
                "folder_tree": False,
                "confirmed_placement": False,
            },
        )

    def test_write_report_is_stable_sorted_json(self) -> None:
        report = build_dream_geometry_suite_report(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "suite.json"
            write_dream_geometry_suite_report(report, output)
            first = output.read_text(encoding="utf-8")
            write_dream_geometry_suite_report(report, output)
            self.assertEqual(first, output.read_text(encoding="utf-8"))
            self.assertIn('"schema": "nollm.dream_geometry_suite.v1"', first)

    def test_runner_script_exits_zero_and_writes_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "suite.json"
            result = run_subprocess(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--repo-root",
                    str(ROOT),
                    "--output",
                    str(output),
                ],
                cwd=REFERENCE_PYTHON,
                timeout_seconds=20,
            )
            self.assertEqual(
                result.returncode,
                0,
                subprocess_failure_message(result, REFERENCE_PYTHON, "run_dream_geometry_suite"),
            )
            self.assertIn("wrote dream geometry suite report", result.stdout)
            data = json.loads(output.read_text(encoding="utf-8"))
            self.assertTrue(data["ok"])

    def test_report_has_no_forbidden_tree_or_ownership_fields(self) -> None:
        report = build_dream_geometry_suite_report(ROOT)
        self.assertFalse(_contains_forbidden_field(report))


def _contains_forbidden_field(value: object) -> bool:
    if isinstance(value, dict):
        return any(key in FORBIDDEN_FIELDS or _contains_forbidden_field(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_contains_forbidden_field(item) for item in value)
    return False


if __name__ == "__main__":
    unittest.main()
