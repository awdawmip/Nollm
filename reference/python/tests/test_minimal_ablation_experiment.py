from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from nollm.minimal_ablation_experiment import (
    DEFAULT_PROFILE,
    MEDIUM_PROFILE,
    ablation_fixture_from_record,
    build_minimal_ablation_report,
    validate_minimal_ablation_report,
)

ROOT = Path(__file__).resolve().parents[3]
REFERENCE_PYTHON = ROOT / "reference" / "python"
FIXTURE = ROOT / "examples" / "openclaw_dream" / "minimal_ablation_fixture.json"


class MinimalAblationExperimentTests(unittest.TestCase):
    def test_n0_does_not_expose_drift_class_or_gravity_tuple(self) -> None:
        report = _report()
        n0 = _condition(report, "N0")

        self.assertEqual(n0["metrics"]["drift_visibility_gain"], 0)
        for item in n0["items"]:
            self.assertNotIn("gravity_report", item)
            self.assertNotIn("geometry_mark", item)
            self.assertFalse(item["visible"]["gravity_report"])

    def test_n2_exposes_rsa_drift_class_and_projection_method(self) -> None:
        report = _report()
        n2 = _condition(report, "N2")
        first = n2["items"][0]

        self.assertTrue(first["visible"]["gravity_report"])
        gravity = first["gravity_report"]
        for key in ("R_column_ring", "S_scale_delta", "A_anchor_similarity", "drift_class", "projection_method"):
            self.assertIn(key, gravity)
        self.assertGreater(n2["metrics"]["drift_visibility_gain"], 0)

    def test_n3_exposes_return_vector_placeholder_without_commanding_return(self) -> None:
        report = _report()
        n3 = _condition(report, "N3")

        self.assertGreater(n3["metrics"]["return_vector_visible"], 0)
        for item in n3["items"]:
            self.assertTrue(item["return_vector"]["visible"])
            self.assertFalse(item["return_vector"]["commands_return"])

    def test_semantic_break_and_far_weak_are_caution_visible_not_rejected(self) -> None:
        report = _report()
        n2 = _condition(report, "N2")
        caution_classes = {
            item["gravity_report"]["drift_class"]
            for item in n2["items"]
            if item["candidate_action"] == "caution_visible"
        }

        self.assertIn("semantic_break", caution_classes)
        self.assertIn("far_weak", caution_classes)
        self.assertTrue(all(item["candidate_action"] != "rejected" for item in n2["items"]))

    def test_far_coherent_lateral_useful_counts_as_visible_discovery(self) -> None:
        report = _report()
        n2 = _condition(report, "N2")

        self.assertGreater(n2["metrics"]["useful_lateral_discovery_visible"], 0)

    def test_misleading_far_item_contributes_to_over_drift_risk_when_gravity_visible(self) -> None:
        report = _report()
        n0 = _condition(report, "N0")
        n2 = _condition(report, "N2")

        self.assertEqual(n0["metrics"]["over_drift_risk_flagged"], 0)
        self.assertGreater(n2["metrics"]["over_drift_risk_flagged"], 0)

    def test_n4_and_n5_use_decided_profiles_without_changing_default(self) -> None:
        report = _report()
        n4 = _condition(report, "N4")
        n5 = _condition(report, "N5")

        self.assertEqual(n4["profile"], MEDIUM_PROFILE)
        self.assertEqual(n5["profile"], DEFAULT_PROFILE)
        self.assertEqual(report["summary"]["n4_vs_n5"]["medium_practical_profile"], MEDIUM_PROFILE)
        self.assertEqual(report["summary"]["n4_vs_n5"]["default_dream_profile"], DEFAULT_PROFILE)

    def test_report_forbidden_semantics_are_all_false(self) -> None:
        report = _report()

        self.assertTrue(all(value is False for value in report["forbidden_semantics"].values()))
        validate_minimal_ablation_report(report)

    def test_runner_writes_only_to_out_runtime_by_default_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "minimal_ablation_experiment_report.json"
            stdout = subprocess.check_output(
                [
                    sys.executable,
                    "scripts/run_minimal_ablation_experiment.py",
                    "--output",
                    str(output),
                ],
                cwd=REFERENCE_PYTHON,
                text=True,
                timeout=30,
            )

            self.assertIn("wrote minimal ablation experiment report", stdout)
            record = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(record["schema"], "nollm.minimal_ablation_experiment.v1")
            self.assertEqual(record["status"], "experimental_internal_only")

    def test_report_is_deterministic_and_json_primitive(self) -> None:
        first = _report()
        second = _report()

        self.assertEqual(first, second)
        json.dumps(first, sort_keys=True)


def _report() -> dict[str, object]:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return build_minimal_ablation_report(ablation_fixture_from_record(fixture))


def _condition(report: dict[str, object], condition: str) -> dict[str, object]:
    for item in report["conditions"]:  # type: ignore[index]
        if item["condition"] == condition:
            return item
    raise AssertionError(f"missing condition: {condition}")


if __name__ == "__main__":
    unittest.main()
