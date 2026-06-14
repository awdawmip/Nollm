from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from nollm.cli import main
from nollm.filesystem import read_card, read_ledger
from nollm.tool_api import dispatch_tool_request
from test_write_read import init_notebook, write_card


def run_json(args: list[str]) -> tuple[int, dict]:
    output = io.StringIO()
    with redirect_stdout(output):
        code = main(args)
    return code, json.loads(output.getvalue())


class LedgerHistoryTests(unittest.TestCase):
    def test_ledger_filters_by_object_op_actor_type_and_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            first, _ = write_card(notebook, title="First")
            second, _ = write_card(notebook, title="Second")
            first_id = first.rsplit("/", 1)[-1]
            second_id = second.rsplit("/", 1)[-1]
            self.assertEqual(main(["annotate", str(notebook), first_id, "--note", "Human note."]), 0)
            self.assertEqual(
                main(
                    [
                        "annotate",
                        str(notebook),
                        second_id,
                        "--note",
                        "Tool note.",
                        "--actor-type",
                        "tool",
                    ]
                ),
                0,
            )

            code, response = run_json(["ledger", str(notebook), "--object-id", first_id, "--limit", "20"])
            self.assertEqual(code, 0)
            self.assertTrue(response["ok"])
            self.assertEqual(response["filters"]["object_id"], first_id)
            self.assertTrue(all(event["object_id"] == first_id for event in response["events"]))

            code, response = run_json(["ledger", str(notebook), "--op", "annotate_card", "--actor-type", "human", "--limit", "1"])
            self.assertEqual(code, 0)
            self.assertEqual(response["event_count"], 1)
            self.assertEqual(response["events"][0]["op"], "annotate_card")
            self.assertEqual(response["events"][0]["actor_type"], "human")

    def test_ledger_ordering_is_deterministic_and_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            address, _ = write_card(notebook)
            card_id = address.rsplit("/", 1)[-1]
            self.assertEqual(main(["annotate", str(notebook), card_id, "--note", "Note."]), 0)
            ledger_before = read_ledger(notebook)
            files_before = sorted(path.relative_to(notebook).as_posix() for path in notebook.rglob("*") if path.is_file())

            first = run_json(["ledger", str(notebook), "--limit", "20"])[1]
            second = run_json(["ledger", str(notebook), "--limit", "20"])[1]

            self.assertEqual(first, second)
            self.assertEqual(read_ledger(notebook), ledger_before)
            files_after = sorted(path.relative_to(notebook).as_posix() for path in notebook.rglob("*") if path.is_file())
            self.assertEqual(files_after, files_before)
            self.assertEqual(first["events"], sorted(first["events"], key=lambda event: (event["timestamp"], event["event_id"])))
            self.assertNotIn("body", json.dumps(first))

    def test_history_accepts_card_id_and_address_and_includes_annotation_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            address, _ = write_card(notebook)
            card_id = address.rsplit("/", 1)[-1]
            note = "Needs source verification."
            self.assertEqual(main(["annotate", str(notebook), card_id, "--note", note, "--annotation-type", "source_request"]), 0)
            front_before, body_before, _ = read_card(notebook, address)

            for target in (card_id, address):
                with self.subTest(target=target):
                    code, response = run_json(["history", str(notebook), target, "--limit", "20"])
                    self.assertEqual(code, 0)
                    self.assertTrue(response["ok"])
                    self.assertEqual(response["object_id"], card_id)
                    self.assertGreaterEqual(response["event_count"], 2)
                    annotation_events = [event for event in response["events"] if event["op"] == "annotate_card"]
                    self.assertEqual(annotation_events[0]["annotation_type"], "source_request")
                    self.assertEqual(annotation_events[0]["annotation"], note)
                    self.assertNotIn(body_before, json.dumps(response))

            front_after, body_after, _ = read_card(notebook, address)
            self.assertEqual(front_after, front_before)
            self.assertEqual(body_after, body_before)

    def test_history_filter_and_missing_target_structured_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            address, _ = write_card(notebook)
            self.assertEqual(main(["annotate", str(notebook), address, "--note", "Note."]), 0)

            code, response = run_json(["history", str(notebook), address, "--op", "annotate_card"])
            self.assertEqual(code, 0)
            self.assertTrue(all(event["op"] == "annotate_card" for event in response["events"]))

            code, response = run_json(["history", str(notebook), "missing_card"])
            self.assertNotEqual(code, 0)
            self.assertFalse(response["ok"])
            self.assertEqual(response["error"]["code"], "invalid_request")

    def test_tool_ledger_and_history_are_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            address, _ = write_card(notebook)
            card_id = address.rsplit("/", 1)[-1]
            self.assertEqual(main(["annotate", str(notebook), card_id, "--note", "Note."]), 0)
            ledger_before = read_ledger(notebook)
            front_before, body_before, _ = read_card(notebook, address)

            ledger = dispatch_tool_request(
                {
                    "protocol": "nollm.tool.v0.1",
                    "request_id": "req_ledger",
                    "action": "nollm.ledger",
                    "arguments": {"notebook_path": str(notebook), "object_id": card_id, "limit": 20},
                }
            )
            history = dispatch_tool_request(
                {
                    "protocol": "nollm.tool.v0.1",
                    "request_id": "req_history",
                    "action": "nollm.history",
                    "arguments": {"notebook_path": str(notebook), "target": card_id, "limit": 20},
                }
            )

            self.assertTrue(ledger["ok"], ledger)
            self.assertTrue(history["ok"], history)
            self.assertEqual(ledger["request_id"], "req_ledger")
            self.assertEqual(history["request_id"], "req_history")
            self.assertEqual(ledger["ledger_events"], [])
            self.assertEqual(history["ledger_events"], [])
            self.assertEqual(read_ledger(notebook), ledger_before)
            front_after, body_after, _ = read_card(notebook, address)
            self.assertEqual(front_after, front_before)
            self.assertEqual(body_after, body_before)


if __name__ == "__main__":
    unittest.main()
