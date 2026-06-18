from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from nollm.g_series_engineering_closure import (
    SCHEMA,
    STATUS,
    build_g_series_engineering_closure_report,
    write_closure_report,
)

ROOT = Path(__file__).resolve().parents[3]
REFERENCE_PYTHON = ROOT / "reference" / "python"


class GSeriesEngineeringClosureTests(unittest.TestCase):
    def test_closure_report_is_deterministic_json_and_ok(self) -> None:
        first = build_g_series_engineering_closure_report(ROOT)
        second = build_g_series_engineering_closure_report(ROOT, generate_reports=False)

        self.assertEqual(first, second)
        self.assertEqual(first["schema"], SCHEMA)
        self.assertEqual(first["status"], STATUS)
        self.assertIs(first["ok"], True)
        json.dumps(first, sort_keys=True)

    def test_required_artifact_paths_are_checked(self) -> None:
        report = build_g_series_engineering_closure_report(ROOT, generate_reports=False)

        self.assertIn("docs/geometry/G5_REVERSE_COVER_MILP.md", report["artifacts"]["docs"])
        self.assertIn("protocol/GRAVITY_WELL.md", report["artifacts"]["protocols"])
        self.assertIn("out/nollm_runtime/minimal_ablation_experiment_report.json", report["artifacts"]["reports"])

    def test_missing_required_artifact_produces_useful_failure(self) -> None:
        report = build_g_series_engineering_closure_report(
            ROOT,
            generate_reports=False,
            docs=("docs/experiments/DOES_NOT_EXIST.md",),
            protocols=(),
            reports=(),
        )

        self.assertIs(report["ok"], False)
        self.assertIn("missing_docs:docs/experiments/DOES_NOT_EXIST.md", report["failures"])

    def test_forbidden_semantics_remain_false(self) -> None:
        report = build_g_series_engineering_closure_report(ROOT, generate_reports=False)

        self.assertTrue(all(value is False for value in report["forbidden_semantics"].values()))
        self.assertIs(report["forbidden_semantics"]["trust_status_mapping"], False)

    def test_ablation_metrics_are_detected(self) -> None:
        report = build_g_series_engineering_closure_report(ROOT, generate_reports=False)
        ablation = report["metrics_presence"]["ablation"]

        self.assertTrue(ablation["n0_to_n5_present"])
        self.assertTrue(ablation["drift_visibility_gain_present"])
        self.assertTrue(ablation["return_vector_visibility_present"])

    def test_drift_class_is_not_mapped_to_trust_or_status(self) -> None:
        report = build_g_series_engineering_closure_report(ROOT, generate_reports=False)

        self.assertFalse(report["forbidden_semantics"]["trust_status_mapping"])
        self.assertEqual(report["status"], "experimental_internal_only")

    def test_runner_writes_deterministic_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "closure.json"
            stdout = subprocess.check_output(
                [
                    sys.executable,
                    "scripts/run_g_series_engineering_gate.py",
                    "--output",
                    str(output),
                ],
                cwd=REFERENCE_PYTHON,
                text=True,
                timeout=120,
            )

            self.assertIn("wrote g-series engineering closure report", stdout)
            record = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(record["schema"], SCHEMA)
            self.assertTrue(record["ok"])

    def test_write_closure_report_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "closure.json"
            report = build_g_series_engineering_closure_report(ROOT, generate_reports=False)

            write_closure_report(report, output)

            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), report)


if __name__ == "__main__":
    unittest.main()
