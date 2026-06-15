from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

from subprocess_harness import run_subprocess, subprocess_failure_message

from nollm.dream_checks_manifest import (
    REQUIRED_REPORTS,
    build_all_dream_checks_manifest,
    validate_all_dream_checks_manifest,
)


ROOT = Path(__file__).resolve().parents[3]
REFERENCE_PYTHON = ROOT / "reference" / "python"
SCRIPT = REFERENCE_PYTHON / "scripts" / "run_all_dream_geometry_checks.py"


class DreamChecksManifestTests(unittest.TestCase):
    def test_manifest_is_ok_for_current_reports(self) -> None:
        manifest = build_all_dream_checks_manifest(ROOT)
        validate_all_dream_checks_manifest(manifest)
        self.assertTrue(manifest["ok"])

    def test_required_reports_are_included(self) -> None:
        manifest = build_all_dream_checks_manifest(ROOT)
        self.assertEqual(manifest["required_reports"], list(REQUIRED_REPORTS))
        self.assertIn("dream_suite", manifest["components"])
        self.assertIn("real_corpus_dry_run", manifest["components"])

    def test_forbidden_semantics_remain_false(self) -> None:
        manifest = build_all_dream_checks_manifest(ROOT)
        self.assertEqual(
            manifest["forbidden_semantics"],
            {
                "parent_child": False,
                "anchor_ownership": False,
                "folder_tree": False,
                "confirmed_placement": False,
            },
        )

    def test_missing_required_report_produces_not_ok(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _copy_required_reports(root)
            (root / REQUIRED_REPORTS[0]).unlink()
            manifest = build_all_dream_checks_manifest(root)
            self.assertFalse(manifest["ok"])
            self.assertTrue(any("missing required report" in item for item in manifest["warnings"]))

    def test_parent_child_flag_produces_not_ok(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _copy_required_reports(root)
            suite_path = root / REQUIRED_REPORTS[0]
            data = json.loads(suite_path.read_text(encoding="utf-8"))
            data["forbidden_semantics"]["parent_child"] = True
            suite_path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
            manifest = build_all_dream_checks_manifest(root)
            self.assertFalse(manifest["ok"])
            self.assertTrue(manifest["forbidden_semantics"]["parent_child"])

    def test_cli_writes_deterministic_json_and_exits_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "manifest.json"
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
                subprocess_failure_message(result, REFERENCE_PYTHON, "run_all_dream_geometry_checks"),
            )
            first = output.read_text(encoding="utf-8")
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
            self.assertEqual(result.returncode, 0)
            self.assertEqual(first, output.read_text(encoding="utf-8"))
            self.assertIn("wrote all dream checks manifest", result.stdout)


def _copy_required_reports(root: Path) -> None:
    for rel in REQUIRED_REPORTS:
        source = ROOT / rel
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


if __name__ == "__main__":
    unittest.main()
