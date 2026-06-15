from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

from subprocess_harness import run_subprocess, subprocess_failure_message

from nollm.dream_corpus_dry_run import (
    run_real_corpus_dry_run,
    validate_real_corpus_dry_run_report,
)


ROOT = Path(__file__).resolve().parents[3]
REFERENCE_PYTHON = ROOT / "reference" / "python"
SCRIPT = REFERENCE_PYTHON / "scripts" / "run_real_corpus_dream_dry_run.py"


class DreamCorpusDryRunTests(unittest.TestCase):
    def test_output_shape_is_deterministic(self) -> None:
        report = run_real_corpus_dry_run(ROOT, max_files=4)
        validate_real_corpus_dry_run_report(report)
        self.assertEqual(report["mode"], "real_corpus_dry_run")
        self.assertTrue(report["ok"])
        self.assertEqual(json.dumps(report, sort_keys=True), json.dumps(run_real_corpus_dry_run(ROOT, max_files=4), sort_keys=True))

    def test_bounded_file_count(self) -> None:
        report = run_real_corpus_dry_run(ROOT, max_files=3)
        self.assertLessEqual(report["file_count"], 3)
        self.assertEqual(report["file_count"], len(report["processed_paths"]))

    def test_real_markdown_produces_shards_and_placements(self) -> None:
        report = run_real_corpus_dry_run(ROOT, max_files=5)
        self.assertGreater(report["file_count"], 0)
        self.assertGreater(report["shard_count"], 0)
        self.assertEqual(report["shard_count"], report["placement_count"])

    def test_forbidden_semantics_remain_false(self) -> None:
        report = run_real_corpus_dry_run(ROOT, max_files=5)
        self.assertEqual(
            report["forbidden_semantics"],
            {
                "parent_child": False,
                "anchor_ownership": False,
                "folder_tree": False,
                "confirmed_placement": False,
            },
        )

    def test_script_exits_zero_and_writes_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "real_corpus_dry_run_report.json"
            result = run_subprocess(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--repo-root",
                    str(ROOT),
                    "--output",
                    str(output),
                    "--max-files",
                    "4",
                ],
                cwd=REFERENCE_PYTHON,
                timeout_seconds=20,
            )
            self.assertEqual(
                result.returncode,
                0,
                subprocess_failure_message(result, REFERENCE_PYTHON, "run_real_corpus_dream_dry_run"),
            )
            data = json.loads(output.read_text(encoding="utf-8"))
            self.assertTrue(data["ok"])
            self.assertEqual(data["mode"], "real_corpus_dry_run")

    def test_report_fixture_is_valid_json_when_present(self) -> None:
        fixture = ROOT / "examples" / "openclaw_dream" / "real_corpus_dry_run_report.json"
        if fixture.exists():
            data = json.loads(fixture.read_text(encoding="utf-8"))
            validate_real_corpus_dry_run_report(data)


if __name__ == "__main__":
    unittest.main()
