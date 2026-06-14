from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from nollm.cli import main
from nollm.filesystem import read_card, read_ledger, write_card_file
from nollm.tool_api import dispatch_tool_request
from nollm.validation import validate_notebook
from test_write_read import init_notebook, write_card


def run_json(args: list[str]) -> tuple[int, dict]:
    output = io.StringIO()
    with redirect_stdout(output):
        code = main(args)
    return code, json.loads(output.getvalue())


class AnnotationCliTests(unittest.TestCase):
    def test_annotate_appends_ledger_event_without_mutating_card(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            address, _event_id = write_card(notebook)
            card_id = address.rsplit("/", 1)[-1]
            front_before, body_before, _ = read_card(notebook, address)
            ledger_before = read_ledger(notebook)

            code, response = run_json(
                [
                    "annotate",
                    str(notebook),
                    card_id,
                    "--note",
                    "Needs source verification.",
                    "--annotation-type",
                    "source_request",
                ]
            )

            self.assertEqual(code, 0)
            self.assertTrue(response["ok"])
            self.assertEqual(response["object_id"], card_id)
            self.assertEqual(response["annotation_type"], "source_request")
            ledger_after = read_ledger(notebook)
            self.assertEqual(len(ledger_after), len(ledger_before) + 1)
            event = ledger_after[-1]
            self.assertEqual(event["op"], "annotate_card")
            self.assertEqual(event["object_id"], card_id)
            self.assertEqual(event["from_status"], event["to_status"])
            self.assertEqual(event["annotation_type"], "source_request")
            self.assertEqual(event["annotation"], "Needs source verification.")
            front_after, body_after, _ = read_card(notebook, address)
            self.assertEqual(front_after, front_before)
            self.assertEqual(body_after, body_before)
            self.assertEqual(front_after["status"], front_before["status"])
            self.assertEqual(front_after["trust"], front_before["trust"])

    def test_annotate_accepts_memory_address(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            address, _event_id = write_card(notebook)

            code, response = run_json(["annotate", str(notebook), address, "--note", "Address target works."])

            self.assertEqual(code, 0)
            self.assertTrue(response["ok"])
            self.assertEqual(response["object_id"], address.rsplit("/", 1)[-1])

    def test_annotate_invalid_target_appends_no_ledger_event(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            ledger_before = read_ledger(notebook)

            code, response = run_json(["annotate", str(notebook), "missing_card", "--note", "No write."])

            self.assertNotEqual(code, 0)
            self.assertFalse(response["ok"])
            self.assertEqual(response["error"]["code"], "invalid_request")
            self.assertEqual(read_ledger(notebook), ledger_before)

    def test_annotate_rejects_invalid_actor_type_and_annotation_type(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            address, _event_id = write_card(notebook)
            for args, expected in (
                (["--actor-type", "oracle"], "invalid actor_type"),
                (["--annotation-type", "approval"], "invalid annotation_type"),
            ):
                with self.subTest(expected=expected):
                    ledger_before = read_ledger(notebook)
                    code, response = run_json(["annotate", str(notebook), address, "--note", "No write.", *args])
                    self.assertNotEqual(code, 0)
                    self.assertFalse(response["ok"])
                    self.assertIn(expected, response["error"]["message"])
                    self.assertEqual(read_ledger(notebook), ledger_before)

    def test_annotation_does_not_satisfy_confirmed_human_approval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            address, _event_id = write_card(notebook)
            front, body, card_path = read_card(notebook, address)
            front["status"] = "confirmed"
            front["trust"] = "human-approved"
            write_card_file(card_path, front, body)

            code, response = run_json(["annotate", str(notebook), address, "--note", "Human note."])

            self.assertEqual(code, 0)
            self.assertTrue(response["ok"])
            issues = validate_notebook(notebook)
            self.assertTrue(any("lacks human approval" in issue for issue in issues), issues)

    def test_annotations_lists_filters_and_limits_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            address, _event_id = write_card(notebook)
            main(["annotate", str(notebook), address, "--note", "First note.", "--annotation-type", "note"])
            main(["annotate", str(notebook), address, "--note", "Concern.", "--annotation-type", "concern"])
            main(["annotate", str(notebook), address, "--note", "Second note.", "--annotation-type", "note"])

            code, response = run_json(["annotations", str(notebook), address, "--annotation-type", "note", "--limit", "1"])

            self.assertEqual(code, 0)
            self.assertTrue(response["ok"])
            self.assertEqual(response["object_id"], address.rsplit("/", 1)[-1])
            self.assertEqual(response["annotation_count"], 1)
            self.assertEqual(response["annotations"][0]["annotation_type"], "note")
            self.assertEqual(response["annotations"][0]["annotation"], "First note.")
            self.assertNotIn("body", json.dumps(response))

    def test_annotations_missing_card_returns_structured_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)

            code, response = run_json(["annotations", str(notebook), "missing_card"])

            self.assertNotEqual(code, 0)
            self.assertFalse(response["ok"])
            self.assertEqual(response["error"]["code"], "invalid_request")


class AnnotationToolTests(unittest.TestCase):
    def test_tool_annotate_and_annotations_are_ledger_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            address, _event_id = write_card(notebook)
            card_id = address.rsplit("/", 1)[-1]
            front_before, body_before, _ = read_card(notebook, address)
            ledger_before = read_ledger(notebook)

            annotate = dispatch_tool_request(
                {
                    "protocol": "nollm.tool.v0.1",
                    "request_id": "req_annotate",
                    "action": "nollm.annotate",
                    "notebook_path": str(notebook),
                    "input": {
                        "target": card_id,
                        "note": "Needs source verification.",
                        "annotation_type": "source_request",
                        "actor": "operator",
                        "actor_type": "human",
                    },
                }
            )

            self.assertTrue(annotate["ok"], annotate)
            self.assertEqual(annotate["request_id"], "req_annotate")
            self.assertEqual(annotate["action"], "nollm.annotate")
            self.assertEqual(len(annotate["ledger_events"]), 1)
            self.assertEqual(len(read_ledger(notebook)), len(ledger_before) + 1)
            front_after, body_after, _ = read_card(notebook, address)
            self.assertEqual(front_after, front_before)
            self.assertEqual(body_after, body_before)

            annotations = dispatch_tool_request(
                {
                    "protocol": "nollm.tool.v0.1",
                    "request_id": "req_annotations",
                    "action": "nollm.annotations",
                    "notebook_path": str(notebook),
                    "input": {"target": card_id, "limit": 20},
                }
            )

            self.assertTrue(annotations["ok"], annotations)
            self.assertEqual(annotations["request_id"], "req_annotations")
            self.assertEqual(annotations["result"]["annotation_count"], 1)
            self.assertEqual(annotations["result"]["annotations"][0]["annotation"], "Needs source verification.")

    def test_tool_accepts_arguments_envelope_for_annotations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            address, _event_id = write_card(notebook)

            response = dispatch_tool_request(
                {
                    "request_id": "req_arguments",
                    "action": "nollm.annotate",
                    "arguments": {
                        "notebook_path": str(notebook),
                        "target": address,
                        "note": "Arguments envelope works.",
                    },
                }
            )

            self.assertTrue(response["ok"], response)
            event = read_ledger(notebook)[-1]
            self.assertEqual(event["actor"], "operator")
            self.assertEqual(event["actor_type"], "human")

    def test_tool_annotation_errors_are_structured(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            address, _event_id = write_card(notebook)

            response = dispatch_tool_request(
                {
                    "action": "nollm.annotate",
                    "notebook_path": str(notebook),
                    "input": {"target": address, "note": "Bad type.", "annotation_type": "approval"},
                }
            )

            self.assertFalse(response["ok"])
            self.assertEqual(response["error"]["code"], "invalid_request")
            self.assertIn("invalid annotation_type", response["error"]["message"])


if __name__ == "__main__":
    unittest.main()
