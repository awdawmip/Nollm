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
    cleanup_runtime_cache_artifacts,
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

    def test_cleanup_runtime_cache_artifacts_removes_only_runtime_cache(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime_paths = [
                root / "reference" / "python" / "nollm" / "__pycache__" / "x.pyc",
                root / "reference" / "python" / "tests" / "__pycache__" / "y.pyc",
                root / "reference" / "python" / ".pytest_cache" / "README.md",
                root / "loose.pyc",
            ]
            for path in runtime_paths:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("runtime", encoding="utf-8")
            real_report = root / "examples" / "openclaw_dream" / "local_gate_report.json"
            real_report.parent.mkdir(parents=True, exist_ok=True)
            real_report.write_text("{}", encoding="utf-8")

            removed = cleanup_runtime_cache_artifacts(root)

            self.assertEqual(
                removed,
                [
                    "loose.pyc",
                    "reference/python/.pytest_cache",
                    "reference/python/nollm/__pycache__",
                    "reference/python/nollm/__pycache__/x.pyc",
                    "reference/python/tests/__pycache__",
                    "reference/python/tests/__pycache__/y.pyc",
                ],
            )
            self.assertFalse((root / "reference" / "python" / "nollm" / "__pycache__").exists())
            self.assertFalse((root / "reference" / "python" / ".pytest_cache").exists())
            self.assertTrue(real_report.exists())

    def test_package_hygiene_still_catches_real_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _temp_gate_root(Path(tmp))
            (root / "some_snapshot.zip").write_text("blocked", encoding="utf-8")
            result = run_subprocess(
                [
                    sys.executable,
                    str(root / "reference" / "python" / "scripts" / "check_package_hygiene.py"),
                    str(root),
                ],
                cwd=root / "reference" / "python",
                timeout_seconds=20,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("some_snapshot.zip", result.stdout)

    def test_skip_pytest_gate_is_idempotent_with_runtime_cache_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _temp_gate_root(Path(tmp))
            _write_runtime_cache(root)
            first = build_local_gate_report(root, include_pytest=False)
            second = build_local_gate_report(root, include_pytest=False)

            self.assertTrue(first["ok"])
            self.assertTrue(second["ok"])
            self.assertFalse(_has_runtime_cache(root))
            self.assertGreaterEqual(first["runtime_cache_cleanup"]["before_count"], 1)  # type: ignore[index]
            self.assertEqual(second["runtime_cache_cleanup"]["before_count"], 0)  # type: ignore[index]

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
            (root / TRIAGE_REPORTS["golden_regression"]).unlink()
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

    def test_pytest_timeout_does_not_poison_next_skip_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _temp_gate_root(Path(tmp))
            original_run = subprocess.run

            def timeout_pytest(command, **kwargs):  # type: ignore[no-untyped-def]
                if list(command)[-1] == "run_tests.py":
                    _write_runtime_cache(root)
                    raise subprocess.TimeoutExpired("pytest", 1)
                return original_run(command, **kwargs)

            with patch("nollm.local_gate.subprocess.run", side_effect=timeout_pytest):
                timeout_report = build_local_gate_report(root, include_pytest=True, pytest_timeout_seconds=1)

            self.assertFalse(timeout_report["ok"])
            self.assertEqual(timeout_report["components"]["pytest"]["returncode"], -1)  # type: ignore[index]
            self.assertEqual(timeout_report["components"]["pytest"]["detail"], "pytest timed out")  # type: ignore[index]
            self.assertFalse(_has_runtime_cache(root))

            skip_report = build_local_gate_report(root, include_pytest=False)
            self.assertTrue(skip_report["ok"])
            self.assertTrue(skip_report["components"]["package_hygiene"]["ok"])  # type: ignore[index]


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


def _write_runtime_cache(root: Path) -> None:
    paths = [
        root / "reference" / "python" / "nollm" / "__pycache__" / "x.pyc",
        root / "reference" / "python" / "tests" / "__pycache__" / "y.pyc",
        root / "reference" / "python" / ".pytest_cache" / "README.md",
    ]
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("runtime", encoding="utf-8")


def _has_runtime_cache(root: Path) -> bool:
    return any(root.rglob("__pycache__")) or any(root.rglob(".pytest_cache")) or any(root.rglob("*.pyc"))


if __name__ == "__main__":
    unittest.main()
