from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from nollm.gravity import GravityMark, GravityWell
from nollm.mode3_trace_experiment import (
    RecallCandidate,
    build_mode3_trace,
    mode3_trace_fixture_from_record,
    mode3_trace_result_to_record,
    validate_mode3_trace_record,
)

ROOT = Path(__file__).resolve().parents[3]
REFERENCE_PYTHON = ROOT / "reference" / "python"
FIXTURE = ROOT / "examples" / "openclaw_dream" / "mode3_trace_fixture.json"


class Mode3TraceExperimentTests(unittest.TestCase):
    def test_trace_preserves_retrieval_rank_order(self) -> None:
        well, candidates = _fixture()
        reversed_candidates = tuple(reversed(candidates))

        result = build_mode3_trace(well, reversed_candidates)

        self.assertEqual([item.rank for item in result.items], list(range(1, 8)))
        self.assertEqual([item.candidate_id for item in result.items][0], "candidate_core")

    def test_trace_does_not_filter_far_or_semantic_break_candidates(self) -> None:
        well, candidates = _fixture()

        record = mode3_trace_result_to_record(build_mode3_trace(well, candidates))
        classes = {item["gravity_report"]["drift_class"] for item in record["items"]}  # type: ignore[index]
        ids = {item["candidate_id"] for item in record["items"]}  # type: ignore[index]

        self.assertIn("far_coherent", classes)
        self.assertIn("far_weak", classes)
        self.assertIn("semantic_break", classes)
        self.assertIn("unglued", classes)
        self.assertIn("candidate_semantic_break", ids)
        self.assertEqual(record["trace_item_count"], 7)

    def test_every_trace_item_has_gravity_report_and_visibility_hint(self) -> None:
        well, candidates = _fixture()

        record = mode3_trace_result_to_record(build_mode3_trace(well, candidates))

        for item in record["items"]:  # type: ignore[index]
            self.assertIn("gravity_report", item)
            self.assertIn("llm_visibility_hint", item)
            self.assertEqual(item["gravity_report"]["status"], "experimental_internal_only")
        self.assertIn("far_and_weak", [item["llm_visibility_hint"] for item in record["items"]])  # type: ignore[index]

    def test_drift_class_counts_are_deterministic(self) -> None:
        well, candidates = _fixture()

        first = mode3_trace_result_to_record(build_mode3_trace(well, candidates))
        second = mode3_trace_result_to_record(build_mode3_trace(well, tuple(reversed(candidates))))

        expected = {
            "core": 1,
            "far_coherent": 1,
            "far_weak": 1,
            "halo": 1,
            "near_drift": 1,
            "semantic_break": 1,
            "unglued": 1,
        }
        self.assertEqual(first["drift_class_counts"], expected)
        self.assertEqual(second["drift_class_counts"], expected)

    def test_max_r_ignores_null_values(self) -> None:
        well, candidates = _fixture()

        record = mode3_trace_result_to_record(build_mode3_trace(well, candidates))

        self.assertEqual(record["max_R_column_ring"], 5)
        null_r_items = [item for item in record["items"] if item["gravity_report"]["R_column_ring"] is None]  # type: ignore[index]
        self.assertEqual(len(null_r_items), 1)

    def test_output_is_json_primitive_serializable(self) -> None:
        well, candidates = _fixture()

        record = mode3_trace_result_to_record(build_mode3_trace(well, candidates, max_items=3))

        validate_mode3_trace_record(record)
        self.assertEqual(record["candidate_count"], 3)
        self.assertEqual(record["trace_item_count"], 3)
        json.dumps(record, sort_keys=True)

    def test_no_field_maps_drift_to_trust_status_or_writeback(self) -> None:
        well, candidates = _fixture()
        record = mode3_trace_result_to_record(build_mode3_trace(well, candidates))
        forbidden = {"trust", "memory_status", "write_permission", "rejection"}

        self.assertTrue(forbidden.isdisjoint(_collect_keys(record)))
        self.assertEqual(record["status"], "experimental_internal_only")

    def test_runner_writes_under_out_runtime_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "mode3_trace_experiment_report.json"
            stdout = subprocess.check_output(
                [
                    sys.executable,
                    "scripts/run_mode3_trace_experiment.py",
                    "--output",
                    str(output),
                ],
                cwd=REFERENCE_PYTHON,
                text=True,
                timeout=30,
            )

            self.assertIn("wrote mode3 trace experiment report", stdout)
            self.assertTrue(output.exists())
            record = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(record["schema"], "nollm.mode3_trace_experiment.v1")

    def test_candidate_validation_rejects_invalid_records(self) -> None:
        with self.assertRaises(ValueError):
            RecallCandidate(
                candidate_id="",
                text="text",
                score=1.0,
                rank=1,
                gravity_mark=_mark(),
            )
        with self.assertRaises(ValueError):
            build_mode3_trace(_well(), [_candidate(rank=1)], max_items=0)


def _fixture() -> tuple[GravityWell, tuple[RecallCandidate, ...]]:
    return mode3_trace_fixture_from_record(json.loads(FIXTURE.read_text(encoding="utf-8")))


def _well() -> GravityWell:
    return GravityWell(
        well_id="gw",
        entry_query="entry",
        geometry_profile="default_dream",
        chart_id="chart",
        layer=0,
        q=0,
        r=0,
        anchor_vector={"a": 1.0},
    )


def _mark() -> GravityMark:
    return GravityMark(
        content_id="candidate",
        geometry_profile="default_dream",
        chart_id="chart",
        layer=0,
        q=0,
        r=0,
        anchor_vector={"a": 1.0},
    )


def _candidate(rank: int) -> RecallCandidate:
    return RecallCandidate(
        candidate_id=f"candidate_{rank}",
        text="text",
        score=1.0,
        rank=rank,
        gravity_mark=_mark(),
    )


def _collect_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        keys = set(value)
        for item in value.values():
            keys.update(_collect_keys(item))
        return keys
    if isinstance(value, list):
        keys: set[str] = set()
        for item in value:
            keys.update(_collect_keys(item))
        return keys
    return set()


if __name__ == "__main__":
    unittest.main()
