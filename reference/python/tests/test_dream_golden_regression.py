from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

from subprocess_harness import run_subprocess

from nollm.dream_golden_regression import (
    GOLDEN_REPORTS,
    normalize_report,
    run_golden_regression,
)


ROOT = Path(__file__).resolve().parents[3]
REFERENCE_PYTHON = ROOT / "reference" / "python"
SCRIPT = REFERENCE_PYTHON / "scripts" / "run_dream_golden_regression.py"
SOURCE_REPORTS = (
    "examples/openclaw_dream/dream_suite_report.json",
    "examples/openclaw_dream/real_corpus_dry_run_report.json",
    "examples/openclaw_dream/all_dream_checks_manifest.json",
)
SOURCE_DIRS = (
    "examples/openclaw_dream/batch",
)
SOURCE_FILES = (
    "examples/openclaw_dream/shards.json",
    "examples/openclaw_dream/placements.json",
    "README.md",
    "ARCHITECTURE.md",
    "ROADMAP.md",
    "protocol/DREAM_SHARD.md",
    "protocol/DREAM_PLACEMENT.md",
    "protocol/DREAM_SCALE_SCAN.md",
    "protocol/CLUSTER_PRESSURE.md",
    "docs/geometry/D1_PURE_GEOMETRY_KERNEL.md",
    "docs/geometry/D2_LOCAL_CHART_AND_GLUING_PROPOSAL.md",
    "docs/experiments/E4_ONE_COMMAND_DREAM_GEOMETRY_SUITE.md",
)


class DreamGoldenRegressionTests(unittest.TestCase):
    def test_update_creates_golden_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _temp_repo(Path(tmp))
            result = run_golden_regression(root, update=True)
            self.assertTrue(result["ok"])
            for rel_path in GOLDEN_REPORTS.values():
                self.assertTrue((root / rel_path).exists())

    def test_compare_passes_immediately_after_update(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _temp_repo(Path(tmp))
            run_golden_regression(root, update=True)
            result = run_golden_regression(root, update=False)
            self.assertTrue(result["ok"])
            self.assertEqual(result["failed_report_count"], 0)

    def test_modifying_golden_file_causes_compare_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _temp_repo(Path(tmp))
            run_golden_regression(root, update=True)
            target = root / GOLDEN_REPORTS["dream_suite_report"]
            data = json.loads(target.read_text(encoding="utf-8"))
            data["ok"] = False
            target.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
            result = run_golden_regression(root, update=False)
            self.assertFalse(result["ok"])
            self.assertEqual(result["failed_report_count"], 1)

    def test_normalized_report_keeps_forbidden_semantics(self) -> None:
        report = json.loads((ROOT / "examples" / "openclaw_dream" / "dream_suite_report.json").read_text(encoding="utf-8"))
        normalized = normalize_report(report, ROOT)
        self.assertIn("forbidden_semantics", normalized)

    def test_cli_passes_and_fails_on_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _temp_repo(Path(tmp) / "repo")
            output = Path(tmp) / "golden_regression.json"
            update = run_subprocess(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--repo-root",
                    str(root),
                    "--output",
                    str(output),
                    "--update",
                ],
                cwd=REFERENCE_PYTHON,
                timeout_seconds=30,
            )
            self.assertEqual(update.returncode, 0)
            compare = run_subprocess(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--repo-root",
                    str(root),
                    "--output",
                    str(output),
                ],
                cwd=REFERENCE_PYTHON,
                timeout_seconds=30,
            )
            self.assertEqual(compare.returncode, 0)
            target = root / GOLDEN_REPORTS["local_gate_report"]
            data = json.loads(target.read_text(encoding="utf-8"))
            data["ok"] = False
            target.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
            mismatch = run_subprocess(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--repo-root",
                    str(root),
                    "--output",
                    str(output),
                ],
                cwd=REFERENCE_PYTHON,
                timeout_seconds=30,
            )
            self.assertNotEqual(mismatch.returncode, 0)

    def test_outputs_do_not_use_ownership_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _temp_repo(Path(tmp))
            result = run_golden_regression(root, update=True)
            encoded = json.dumps(result, sort_keys=True)
            for forbidden in ("parent_id", "children", "folder", "owner_anchor", "belongs_to_anchor"):
                self.assertNotIn(forbidden, encoded)


def _temp_repo(root: Path) -> Path:
    for rel_path in SOURCE_REPORTS:
        source = ROOT / rel_path
        target = root / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    for rel_path in SOURCE_FILES:
        source = ROOT / rel_path
        target = root / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    for rel_path in SOURCE_DIRS:
        source = ROOT / rel_path
        target = root / rel_path
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source, target)
    scripts = root / "reference" / "python" / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(
        ROOT / "reference" / "python" / "scripts" / "check_package_hygiene.py",
        scripts / "check_package_hygiene.py",
    )
    return root


if __name__ == "__main__":
    unittest.main()
