from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

from subprocess_harness import run_subprocess, subprocess_failure_message

from nollm.dream_triage import (
    TRIAGE_REPORTS,
    build_dream_triage_report,
    render_dream_triage_markdown,
    validate_dream_triage_report,
)


ROOT = Path(__file__).resolve().parents[3]
REFERENCE_PYTHON = ROOT / "reference" / "python"
SCRIPT = REFERENCE_PYTHON / "scripts" / "run_dream_failure_triage.py"


class DreamTriageTests(unittest.TestCase):
    def test_builds_triage_report_from_current_fixture_reports(self) -> None:
        report = build_dream_triage_report(ROOT)
        validate_dream_triage_report(report)
        self.assertTrue(report["ok"])
        self.assertEqual(report["summary"]["report_count"], 5)

    def test_report_is_json_primitive_serializable(self) -> None:
        report = build_dream_triage_report(ROOT)
        json.dumps(report, sort_keys=True)

    def test_markdown_rendering_is_deterministic(self) -> None:
        report = build_dream_triage_report(ROOT)
        self.assertEqual(render_dream_triage_markdown(report), render_dream_triage_markdown(report))

    def test_forbidden_flags_are_aggregated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _temp_reports(Path(tmp))
            suite = root / TRIAGE_REPORTS["dream_suite"]
            data = json.loads(suite.read_text(encoding="utf-8"))
            data["forbidden_semantics"]["parent_child"] = True
            suite.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
            report = build_dream_triage_report(root)
            self.assertFalse(report["ok"])
            self.assertTrue(report["forbidden_semantics"]["parent_child"])

    def test_missing_report_is_recorded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _temp_reports(Path(tmp))
            (root / TRIAGE_REPORTS["local_gate"]).unlink()
            report = build_dream_triage_report(root)
            self.assertFalse(report["ok"])
            self.assertFalse(report["reports"]["local_gate"]["present"])
            self.assertEqual(report["summary"]["missing_report_count"], 1)

    def test_cli_writes_markdown_and_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _temp_reports(Path(tmp) / "repo")
            md_output = Path(tmp) / "triage.md"
            json_output = Path(tmp) / "triage.json"
            result = run_subprocess(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--repo-root",
                    str(root),
                    "--output",
                    str(md_output),
                    "--json-output",
                    str(json_output),
                ],
                cwd=REFERENCE_PYTHON,
                timeout_seconds=20,
            )
            self.assertEqual(
                result.returncode,
                0,
                subprocess_failure_message(result, REFERENCE_PYTHON, "run_dream_failure_triage"),
            )
            self.assertIn("# Nollm Dream Geometry Failure Triage", md_output.read_text(encoding="utf-8"))
            self.assertTrue(json.loads(json_output.read_text(encoding="utf-8"))["ok"])

    def test_generated_report_avoids_ownership_semantics(self) -> None:
        report = build_dream_triage_report(ROOT)
        markdown = render_dream_triage_markdown(report)
        for forbidden in ("parent_id", "| children |", "| folder |", "owner_anchor", "belongs_to_anchor"):
            self.assertNotIn(forbidden, markdown)


def _temp_reports(root: Path) -> Path:
    for rel_path in TRIAGE_REPORTS.values():
        source = ROOT / rel_path
        target = root / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    return root


if __name__ == "__main__":
    unittest.main()
