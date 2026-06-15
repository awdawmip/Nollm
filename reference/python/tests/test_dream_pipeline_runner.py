from __future__ import annotations

import json
import sys
from pathlib import Path
import tempfile
import unittest

from subprocess_harness import run_subprocess, subprocess_failure_message

from nollm.dream_pipeline import (
    FORBIDDEN_REPORT_FIELDS,
    build_dream_geometry_run_report,
    dream_geometry_run_report_to_record,
    load_dream_geometry_fixture,
    validate_dream_geometry_run_report,
)


ROOT = Path(__file__).resolve().parents[3]
REFERENCE_PYTHON = ROOT / "reference" / "python"
SCRIPT = REFERENCE_PYTHON / "scripts" / "run_openclaw_dream_pipeline.py"


class DreamPipelineRunnerTests(unittest.TestCase):
    def test_fixture_loads_and_report_is_json_primitive(self) -> None:
        shards, placements = load_dream_geometry_fixture(ROOT)
        report = build_dream_geometry_run_report(shards, placements)
        encoded = json.dumps(dream_geometry_run_report_to_record(report), sort_keys=True)
        self.assertIn("openclaw-dream-e1", encoded)

    def test_report_contains_all_fixture_shards(self) -> None:
        shards, placements = load_dream_geometry_fixture(ROOT)
        report = build_dream_geometry_run_report(shards, placements)
        self.assertEqual(
            {record["shard_id"] for record in report["shards"]},
            {record["shard_id"] for record in shards},
        )

    def test_ranked_placements_are_deterministic_with_reversed_input(self) -> None:
        shards, placements = load_dream_geometry_fixture(ROOT)
        first = build_dream_geometry_run_report(shards, placements)
        second = build_dream_geometry_run_report(shards, list(reversed(placements)))
        self.assertEqual(first["ranked_placements"], second["ranked_placements"])

    def test_invalid_placement_shard_id_raises(self) -> None:
        shards, placements = load_dream_geometry_fixture(ROOT)
        bad = [dict(record) for record in placements]
        bad[0]["shard_id"] = "missing-shard"
        with self.assertRaises(ValueError):
            build_dream_geometry_run_report(shards, bad)

    def test_forbidden_tree_fields_are_absent_recursively(self) -> None:
        shards, placements = load_dream_geometry_fixture(ROOT)
        report = build_dream_geometry_run_report(shards, placements)
        self.assertFalse(_contains_forbidden_field(report))
        poisoned = dict(report)
        poisoned["parent_id"] = "bad"
        with self.assertRaises(ValueError):
            validate_dream_geometry_run_report(poisoned)

    def test_script_writes_report_to_temporary_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "dream_run_report.json"
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
                subprocess_failure_message(result, REFERENCE_PYTHON, "run_openclaw_dream_pipeline"),
            )
            self.assertIn("wrote dream geometry report", result.stdout)
            data = json.loads(output.read_text(encoding="utf-8"))
            for key in (
                "run_id",
                "status",
                "chart_id",
                "shards",
                "ranked_placements",
                "pressure_samples",
                "coarse_emergence_candidates",
                "scale_scan_plans",
                "parameter_results",
                "warnings",
            ):
                self.assertIn(key, data)


def _contains_forbidden_field(value: object) -> bool:
    if isinstance(value, dict):
        return any(key in FORBIDDEN_REPORT_FIELDS or _contains_forbidden_field(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_contains_forbidden_field(item) for item in value)
    return False


if __name__ == "__main__":
    unittest.main()
