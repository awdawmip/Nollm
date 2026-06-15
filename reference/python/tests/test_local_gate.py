from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from subprocess_harness import run_subprocess, subprocess_failure_message

from nollm.dream_checks_manifest import REQUIRED_REPORTS
from nollm.dream_triage import TRIAGE_REPORTS
from nollm.local_gate import (
    _run_component,
    aggregate_local_gate_report,
    build_local_gate_report,
    validate_local_gate_report,
)


ROOT = Path(__file__).resolve().parents[3]
REFERENCE_PYTHON = ROOT / "reference" / "python"
SCRIPT = REFERENCE_PYTHON / "scripts" / "run_nollm_local_gate.py"


class LocalGateTests(unittest.TestCase):
    def test_report_has_stable_schema_and_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _temp_gate_root(Path(tmp))
            report = build_local_gate_report(root, include_pytest=False)
            validate_local_gate_report(report)
            self.assertEqual(report["schema"], "nollm.local_gate.v1")
            self.assertEqual(report["status"], "experimental_internal_only")

    def test_skip_pytest_records_included_false(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _temp_gate_root(Path(tmp))
            report = build_local_gate_report(root, include_pytest=False)
            self.assertFalse(report["components"]["pytest"]["included"])

    def test_dream_checks_manifest_result_is_included_and_ok(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _temp_gate_root(Path(tmp))
            report = build_local_gate_report(root, include_pytest=False)
            self.assertTrue(report["components"]["dream_checks_manifest"]["ok"])

    def test_dream_failure_triage_result_is_included_and_ok(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _temp_gate_root(Path(tmp))
            report = build_local_gate_report(root, include_pytest=False)
            self.assertTrue(report["components"]["dream_failure_triage"]["ok"])

    def test_gate_fails_when_dream_failure_triage_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _temp_gate_root(Path(tmp))
            (root / TRIAGE_REPORTS["local_gate"]).unlink()
            report = build_local_gate_report(root, include_pytest=False)
            self.assertFalse(report["ok"])
            self.assertFalse(report["components"]["dream_failure_triage"]["ok"])

    def test_forbidden_semantics_remain_false(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _temp_gate_root(Path(tmp))
            report = build_local_gate_report(root, include_pytest=False)
            self.assertEqual(
                report["forbidden_semantics"],
                {
                    "parent_child": False,
                    "anchor_ownership": False,
                    "folder_tree": False,
                    "confirmed_placement": False,
                },
            )

    def test_cli_writes_json_and_exits_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _temp_gate_root(Path(tmp) / "repo")
            output = Path(tmp) / "gate.json"
            result = run_subprocess(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--repo-root",
                    str(root),
                    "--output",
                    str(output),
                    "--skip-pytest",
                ],
                cwd=REFERENCE_PYTHON,
                timeout_seconds=20,
            )
            self.assertEqual(
                result.returncode,
                0,
                subprocess_failure_message(result, REFERENCE_PYTHON, "run_nollm_local_gate"),
            )
            data = json.loads(output.read_text(encoding="utf-8"))
            self.assertTrue(data["ok"])
            self.assertFalse(data["components"]["pytest"]["included"])

    def test_failure_propagates_from_component_aggregation(self) -> None:
        report = aggregate_local_gate_report(
            {
                "package_hygiene": {"ok": True, "included": True},
                "dream_checks_manifest": {"ok": False, "included": True},
                "pytest": {"ok": True, "included": False},
            },
            {
                "parent_child": False,
                "anchor_ownership": False,
                "folder_tree": False,
                "confirmed_placement": False,
            },
        )
        self.assertFalse(report["ok"])

    def test_pytest_timeout_is_reported(self) -> None:
        with patch("nollm.local_gate.subprocess.run", side_effect=subprocess.TimeoutExpired("pytest", 3)):
            component = _run_component(
                [sys.executable, "run_tests.py"],
                cwd=REFERENCE_PYTHON,
                detail="pytest",
                timeout_seconds=3,
            ).to_record()
        self.assertFalse(component["ok"])
        self.assertEqual(component["returncode"], -1)
        self.assertEqual(component["detail"], "pytest timed out")
        self.assertEqual(component["timeout_seconds"], 3)


def _temp_gate_root(root: Path) -> Path:
    for rel in sorted(set(REQUIRED_REPORTS).union(TRIAGE_REPORTS.values())):
        source = ROOT / rel
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    script_source = ROOT / "reference" / "python" / "scripts" / "check_package_hygiene.py"
    script_target = root / "reference" / "python" / "scripts" / "check_package_hygiene.py"
    script_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(script_source, script_target)
    return root


if __name__ == "__main__":
    unittest.main()
