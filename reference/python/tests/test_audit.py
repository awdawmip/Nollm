from __future__ import annotations

import io
import json
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from nollm.audit import build_audit_report, compare_audit_reports, validate_audit_report_shape
from nollm.cli import main
from nollm.filesystem import read_ledger
from cli_harness import run_cli
from subprocess_harness import subprocess_failure_message
from test_write_read import init_notebook, write_card


ROOT = Path(__file__).resolve().parents[3]
REFERENCE_PYTHON = ROOT / "reference" / "python"


def run_cli_json(args: list[str]) -> dict:
    output = io.StringIO()
    with redirect_stdout(output):
        code = main(args)
    assert code == 0
    return json.loads(output.getvalue())


def run_cli_text(args: list[str]) -> str:
    output = io.StringIO()
    with redirect_stdout(output):
        code = main(args)
    assert code == 0
    return output.getvalue()


class AuditTests(unittest.TestCase):
    def test_build_audit_report_passes_schema_checker(self) -> None:
        report = build_audit_report(ROOT / "examples" / "openclaw")

        self.assertEqual(validate_audit_report_shape(report), [])

    def test_schema_checker_detects_missing_top_level_section(self) -> None:
        report = build_audit_report(ROOT / "examples" / "openclaw")
        report.pop("honeycomb")

        issues = validate_audit_report_shape(report)

        self.assertIn("missing top-level section: honeycomb", issues)

    def test_schema_checker_requires_annotations_section(self) -> None:
        report = build_audit_report(ROOT / "examples" / "openclaw")
        report.pop("annotations")

        issues = validate_audit_report_shape(report)

        self.assertIn("missing top-level section: annotations", issues)

    def test_schema_checker_detects_missing_nested_field(self) -> None:
        report = build_audit_report(ROOT / "examples" / "openclaw")
        report["notebook"].pop("cards")

        issues = validate_audit_report_shape(report)

        self.assertIn("missing field: notebook.cards", issues)

    def test_schema_checker_requires_boolean_boundary_flags(self) -> None:
        report = build_audit_report(ROOT / "examples" / "openclaw")
        report["boundaries"]["uses_sqlite"] = "false"

        issues = validate_audit_report_shape(report)

        self.assertIn("invalid type: boundaries.uses_sqlite expected boolean", issues)

    def test_audit_returns_valid_json_for_openclaw(self) -> None:
        report = run_cli_json(["audit", str(ROOT / "examples" / "openclaw")])

        self.assertEqual(validate_audit_report_shape(report), [])
        self.assertTrue(report["validation"]["pass"])
        self.assertEqual(report["validation"]["issue_count"], 0)
        self.assertEqual(report["notebook"]["name"], "openclaw")
        self.assertEqual(report["notebook"]["cards"], 2)
        self.assertEqual(report["notebook"]["anchors"], 4)
        self.assertEqual(report["notebook"]["ledger_events"], 2)
        self.assertEqual(report["notebook"]["recall_digests"], 1)
        self.assertEqual(report["cards"]["by_status"], {"confirmed": 2})
        self.assertEqual(report["cards"]["by_type"], {"decision": 2})
        self.assertEqual(report["cards"]["by_trust"], {"human-approved": 2})
        self.assertEqual(report["cards"]["by_source"], {"human_decision": 2})
        self.assertEqual(report["cards"]["by_layer"], {"1": 1})
        self.assertEqual(
            report["annotations"],
            {
                "annotation_event_count": 0,
                "annotated_card_count": 0,
                "by_annotation_type": {},
                "by_actor_type": {},
                "cards_with_annotations": {},
            },
        )

    def test_audit_includes_required_sections_and_metadata_summaries(self) -> None:
        report = run_cli_json(["audit", str(ROOT / "examples" / "openclaw")])

        for section in (
            "validation",
            "notebook",
            "cards",
            "honeycomb",
            "anchor_fields",
            "recall_digests",
            "ledger",
            "annotations",
            "boundaries",
        ):
            self.assertIn(section, report)
        self.assertEqual(report["honeycomb"]["cards_with_layer"], 1)
        self.assertEqual(report["honeycomb"]["cards_with_hex"], 1)
        self.assertEqual(report["honeycomb"]["cards_with_anchor_fields"], 1)
        self.assertEqual(report["honeycomb"]["cards_with_scale_links"], 1)
        self.assertEqual(report["honeycomb"]["invalid_honeycomb_metadata_count"], 0)
        self.assertEqual(report["anchor_fields"]["anchor_count"], 4)
        self.assertEqual(report["anchor_fields"]["anchor_field_usage_counts"]["architecture_is_index"], 1)
        self.assertEqual(report["recall_digests"]["memory_intent_counts"], {"recall_focus": 1})
        self.assertEqual(report["recall_digests"]["digests_with_scale_path"], 1)
        self.assertEqual(report["ledger"]["ledger_event_count"], 2)
        self.assertEqual(report["ledger"]["status_transition_count"], 2)
        self.assertEqual(report["ledger"]["missing_referenced_object_count"], 0)

    def test_cli_output_passes_schema_checker(self) -> None:
        completed = run_cli(["audit", "../../examples/openclaw"], cwd=REFERENCE_PYTHON)
        self.assertEqual(completed.returncode, 0, subprocess_failure_message(completed, REFERENCE_PYTHON))
        report = json.loads(completed.stdout)

        self.assertEqual(validate_audit_report_shape(report), [])

    def test_tool_output_passes_schema_checker(self) -> None:
        completed = run_cli(["tool", "../../examples/tool_requests/audit_openclaw.json"], cwd=REFERENCE_PYTHON)
        self.assertEqual(completed.returncode, 0, subprocess_failure_message(completed, REFERENCE_PYTHON, "audit_openclaw.json"))
        response = json.loads(completed.stdout)

        self.assertTrue(response["ok"])
        self.assertEqual(validate_audit_report_shape(response["result"]), [])

    def test_openclaw_golden_audit_snapshot_is_stable(self) -> None:
        golden_path = ROOT / "examples" / "audit_reports" / "openclaw_audit.json"
        golden = json.loads(golden_path.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            notebook = Path(tmp) / "openclaw"
            shutil.copytree(ROOT / "examples" / "openclaw", notebook)
            remove_generated_recall_artifacts(notebook)
            completed = run_cli(["audit", str(notebook)], cwd=REFERENCE_PYTHON)
            self.assertEqual(completed.returncode, 0, subprocess_failure_message(completed, REFERENCE_PYTHON))
            current = json.loads(completed.stdout)
            current["notebook"]["path"] = golden["notebook"]["path"]

        self.assertEqual(validate_audit_report_shape(golden), [])
        self.assertEqual(current, golden)

    def test_static_tool_response_example_passes_schema_checker(self) -> None:
        path = ROOT / "examples" / "tool_responses" / "audit_openclaw_response.json"
        response = json.loads(path.read_text(encoding="utf-8"))

        self.assertTrue(response["ok"])
        self.assertEqual(validate_audit_report_shape(response["result"]), [])
        self.assertEqual(set(response["result"]["boundaries"]), set(build_audit_report(ROOT / "examples" / "openclaw")["boundaries"]))
        response_text = path.read_text(encoding="utf-8").lower()
        self.assertNotIn("audit is recall", response_text)
        self.assertNotIn("audit is memory", response_text)

    def test_boundary_flags_are_false(self) -> None:
        report = run_cli_json(["audit", str(ROOT / "examples" / "openclaw")])

        self.assertTrue(report["boundaries"])
        self.assertTrue(all(value is False for value in report["boundaries"].values()))

    def test_audit_is_read_only_and_does_not_create_files_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            write_card(notebook)
            ledger_before = read_ledger(notebook)
            files_before = sorted(path.relative_to(notebook).as_posix() for path in notebook.rglob("*") if path.is_file())

            report = run_cli_json(["audit", str(notebook)])

            self.assertTrue(report["validation"]["pass"])
            self.assertEqual(read_ledger(notebook), ledger_before)
            files_after = sorted(path.relative_to(notebook).as_posix() for path in notebook.rglob("*") if path.is_file())
            self.assertEqual(files_after, files_before)

    def test_audit_counts_annotations_without_using_text_as_memory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            address, _event_id = write_card(notebook)
            card_id = address.rsplit("/", 1)[-1]
            self.assertEqual(
                main(
                    [
                        "annotate",
                        str(notebook),
                        card_id,
                        "--note",
                        "Needs source verification.",
                        "--annotation-type",
                        "source_request",
                        "--actor-type",
                        "human",
                    ]
                ),
                0,
            )
            self.assertEqual(
                main(
                    [
                        "annotate",
                        str(notebook),
                        card_id,
                        "--note",
                        "Check concern.",
                        "--annotation-type",
                        "concern",
                        "--actor-type",
                        "tool",
                    ]
                ),
                0,
            )

            report = build_audit_report(notebook)

            self.assertEqual(report["annotations"]["annotation_event_count"], 2)
            self.assertEqual(report["annotations"]["annotated_card_count"], 1)
            self.assertEqual(report["annotations"]["by_annotation_type"], {"concern": 1, "source_request": 1})
            self.assertEqual(report["annotations"]["by_actor_type"], {"human": 1, "tool": 1})
            self.assertEqual(report["annotations"]["cards_with_annotations"], {card_id: 2})
            self.assertNotIn("Needs source verification.", json.dumps(report))

    def test_audit_out_writes_file_without_ledger_event(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            write_card(notebook)
            ledger_before = read_ledger(notebook)
            out_path = Path(tmp) / "audit.json"

            run_cli_text(["audit", str(notebook), "--out", str(out_path)])

            self.assertTrue(out_path.exists())
            report = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertTrue(report["validation"]["pass"])
            self.assertEqual(read_ledger(notebook), ledger_before)

    def test_markdown_audit_is_deterministic_and_includes_summaries(self) -> None:
        notebook = str(ROOT / "examples" / "openclaw")

        first = run_cli_text(["audit", notebook, "--format", "markdown"])
        second = run_cli_text(["audit", notebook, "--format", "markdown"])

        self.assertEqual(first, second)
        self.assertIn("## Validation", first)
        self.assertIn("## Boundaries", first)

    def test_audit_check_reports_no_drift_for_openclaw_snapshot(self) -> None:
        completed = run_cli(
            ["audit-check", "../../examples/openclaw", "--against", "../../examples/audit_reports/openclaw_audit.json"],
            cwd=REFERENCE_PYTHON,
        )
        self.assertEqual(completed.returncode, 0, subprocess_failure_message(completed, REFERENCE_PYTHON))
        response = json.loads(completed.stdout)

        self.assertTrue(response["ok"])
        self.assertTrue(response["matches"])
        self.assertEqual(response["drift_count"], 0)
        self.assertEqual(response["drifts"], [])
        self.assertEqual(response["ignored_fields"], ["notebook.path"])

    def test_audit_check_detects_snapshot_drift(self) -> None:
        golden = json.loads((ROOT / "examples" / "audit_reports" / "openclaw_audit.json").read_text(encoding="utf-8"))
        golden["notebook"]["cards"] = 3
        with tempfile.TemporaryDirectory() as tmp:
            snapshot = Path(tmp) / "drifted_snapshot.json"
            snapshot.write_text(json.dumps(golden), encoding="utf-8")
            completed = run_cli(["audit-check", "../../examples/openclaw", "--against", str(snapshot)], cwd=REFERENCE_PYTHON)
        self.assertEqual(completed.returncode, 1, subprocess_failure_message(completed, REFERENCE_PYTHON))
        response = json.loads(completed.stdout)

        self.assertTrue(response["ok"])
        self.assertFalse(response["matches"])
        self.assertGreater(response["drift_count"], 0)
        self.assertIn({"path": "notebook.cards", "expected": 3, "actual": 2}, response["drifts"])

    def test_audit_check_returns_schema_error_for_invalid_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            snapshot = Path(tmp) / "invalid_snapshot.json"
            snapshot.write_text(json.dumps({"validation": {"pass": True}}), encoding="utf-8")
            completed = run_cli(["audit-check", "../../examples/openclaw", "--against", str(snapshot)], cwd=REFERENCE_PYTHON)
        self.assertEqual(completed.returncode, 2, subprocess_failure_message(completed, REFERENCE_PYTHON))
        response = json.loads(completed.stdout)

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "invalid_audit_schema")
        self.assertTrue(response["schema_issues"]["expected"])

    def test_audit_check_returns_error_for_unreadable_snapshot(self) -> None:
        missing_snapshot = ROOT / "examples" / "audit_reports" / "missing_snapshot.json"
        completed = run_cli(["audit-check", "../../examples/openclaw", "--against", str(missing_snapshot)], cwd=REFERENCE_PYTHON)
        self.assertEqual(completed.returncode, 2, subprocess_failure_message(completed, REFERENCE_PYTHON))
        response = json.loads(completed.stdout)

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "unreadable_snapshot")

    def test_audit_compare_ignores_notebook_path_only(self) -> None:
        expected = build_audit_report(ROOT / "examples" / "openclaw")
        actual = build_audit_report(ROOT / "examples" / "openclaw")
        actual["notebook"]["path"] = "different/environment/path"

        response = compare_audit_reports(expected, actual)

        self.assertTrue(response["matches"])
        self.assertEqual(response["drift_count"], 0)
        self.assertEqual(response["ignored_fields"], ["notebook.path"])

    def test_audit_check_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = Path(tmp) / "openclaw"
            shutil.copytree(ROOT / "examples" / "openclaw", notebook)
            remove_generated_recall_artifacts(notebook)
            ledger_before = read_ledger(notebook)
            files_before = sorted(path.relative_to(notebook).as_posix() for path in notebook.rglob("*") if path.is_file())

            completed = run_cli(
                ["audit-check", str(notebook), "--against", str(ROOT / "examples" / "audit_reports" / "openclaw_audit.json")],
                cwd=REFERENCE_PYTHON,
            )

            self.assertEqual(completed.returncode, 0, subprocess_failure_message(completed, REFERENCE_PYTHON))
            self.assertEqual(read_ledger(notebook), ledger_before)
            files_after = sorted(path.relative_to(notebook).as_posix() for path in notebook.rglob("*") if path.is_file())
            self.assertEqual(files_after, files_before)
            self.assertEqual(generated_recall_artifacts(notebook), [])

def remove_generated_recall_artifacts(notebook: Path) -> None:
    for pattern in ("recall_*.json", "recall_*.md"):
        for path in (notebook / "recalls").glob(pattern):
            path.unlink()


def generated_recall_artifacts(notebook: Path) -> list[str]:
    recalls = notebook / "recalls"
    return sorted(
        path.name
        for pattern in ("recall_*.json", "recall_*.md")
        for path in recalls.glob(pattern)
    )


if __name__ == "__main__":
    unittest.main()
