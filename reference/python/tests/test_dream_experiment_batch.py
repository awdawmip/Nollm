from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

from subprocess_harness import run_subprocess, subprocess_failure_message

from nollm.dream_experiment_batch import (
    build_batch_experiment_report,
    load_batch_fixture,
    validate_batch_experiment_report,
)


ROOT = Path(__file__).resolve().parents[3]
REFERENCE_PYTHON = ROOT / "reference" / "python"
SCRIPT = REFERENCE_PYTHON / "scripts" / "run_dream_experiment_batch.py"


class DreamExperimentBatchTests(unittest.TestCase):
    def test_batch_fixtures_load(self) -> None:
        fixtures = load_batch_fixture(ROOT)
        self.assertEqual(
            [item["fixture_id"] for item in fixtures],
            [
                "lateral_shift_hint",
                "multi_shard_overlap",
                "parameter_probe",
                "placement_collision",
                "single_shard_sparse",
            ],
        )

    def test_batch_report_validates(self) -> None:
        report = build_batch_experiment_report(load_batch_fixture(ROOT))
        validate_batch_experiment_report(report)
        self.assertTrue(report["invariants"]["ok"])
        self.assertEqual(report["fixture_count"], 5)

    def test_report_is_deterministic_across_two_builds(self) -> None:
        fixtures = load_batch_fixture(ROOT)
        first = build_batch_experiment_report(fixtures)
        second = build_batch_experiment_report(list(reversed(fixtures)))
        self.assertEqual(
            json.dumps(first, sort_keys=True),
            json.dumps(second, sort_keys=True),
        )

    def test_script_writes_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "batch_report.json"
            result = run_subprocess(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--repo-root",
                    str(ROOT),
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
                timeout_seconds=20,
            )
            self.assertEqual(
                result.returncode,
                0,
                subprocess_failure_message(result, ROOT, "run_dream_experiment_batch"),
            )
            data = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(data["status"], "experimental_candidate")
            self.assertTrue(data["invariants"]["ok"])

    def test_forbidden_tree_field_causes_validation_failure(self) -> None:
        report = build_batch_experiment_report(load_batch_fixture(ROOT))
        report["parent_id"] = "bad"
        with self.assertRaises(ValueError):
            validate_batch_experiment_report(report)

    def test_unknown_placement_shard_id_causes_invariant_failure(self) -> None:
        fixtures = load_batch_fixture(ROOT)
        bad_fixture = dict(fixtures[0])
        bad_placements = [dict(item) for item in bad_fixture["placements"]]
        bad_placements[0]["shard_id"] = "missing-shard"
        bad_fixture["placements"] = bad_placements
        report = build_batch_experiment_report([bad_fixture])
        self.assertFalse(report["invariants"]["ok"])
        messages = [item["message"] for item in report["invariants"]["checks"]]
        self.assertTrue(any("unknown shard_id" in message for message in messages))


if __name__ == "__main__":
    unittest.main()
