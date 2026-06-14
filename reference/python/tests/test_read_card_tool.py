from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from nollm.filesystem import read_card, read_ledger
from nollm.tool_api import dispatch_tool_request
from test_write_read import init_notebook, write_card


class ReadCardToolTests(unittest.TestCase):
    def test_read_card_returns_requested_card_body_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            address, _event_id = write_card(notebook)
            front_before, body_before, _ = read_card(notebook, address)
            ledger_before = read_ledger(notebook)
            files_before = sorted(path.relative_to(notebook).as_posix() for path in notebook.rglob("*") if path.is_file())

            response = dispatch_tool_request(
                {
                    "protocol": "nollm.tool.v0.1",
                    "request_id": "req_read",
                    "action": "nollm.read_card",
                    "arguments": {
                        "notebook_path": str(notebook),
                        "target": address.rsplit("/", 1)[-1],
                    },
                }
            )

            self.assertTrue(response["ok"], response)
            self.assertEqual(response["request_id"], "req_read")
            self.assertEqual(response["ledger_events"], [])
            result = response["result"]
            self.assertTrue(result["ok"])
            self.assertEqual(result["id"], address.rsplit("/", 1)[-1])
            self.assertEqual(result["address"], address)
            self.assertEqual(result["frontmatter"], front_before)
            self.assertEqual(result["body"], body_before)
            self.assert_no_context_fields(result)
            self.assertEqual(read_ledger(notebook), ledger_before)
            files_after = sorted(path.relative_to(notebook).as_posix() for path in notebook.rglob("*") if path.is_file())
            self.assertEqual(files_after, files_before)

    def test_read_card_include_flags_omit_body_or_frontmatter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            address, _event_id = write_card(notebook)
            for payload, omitted in (
                ({"target": address, "include_body": False}, "body"),
                ({"target": address, "include_frontmatter": False}, "frontmatter"),
            ):
                with self.subTest(omitted=omitted):
                    payload["notebook_path"] = str(notebook)
                    response = dispatch_tool_request(
                        {
                            "protocol": "nollm.tool.v0.1",
                            "action": "nollm.read_card",
                            "arguments": payload,
                        }
                    )
                    self.assertTrue(response["ok"], response)
                    self.assertNotIn(omitted, response["result"])
                    self.assert_no_context_fields(response["result"])

    def test_read_card_accepts_legacy_card_id_field(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            address, _event_id = write_card(notebook)
            response = dispatch_tool_request(
                {
                    "protocol": "nollm.tool.v0.1",
                    "action": "nollm.read_card",
                    "notebook_path": str(notebook),
                    "input": {"card_id_or_address": address},
                }
            )

            self.assertTrue(response["ok"], response)
            self.assertEqual(response["result"]["id"], address.rsplit("/", 1)[-1])

    def test_read_card_missing_card_returns_structured_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            response = dispatch_tool_request(
                {
                    "protocol": "nollm.tool.v0.1",
                    "action": "nollm.read_card",
                    "notebook_path": str(notebook),
                    "input": {"target": "missing_card"},
                }
            )

            self.assertFalse(response["ok"])
            self.assertEqual(response["error"]["code"], "invalid_request")

    def test_read_card_does_not_return_annotation_text_unless_card_body_contains_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            address, _event_id = write_card(notebook)
            note = "Operator-only annotation text."
            dispatch_tool_request(
                {
                    "protocol": "nollm.tool.v0.1",
                    "action": "nollm.annotate",
                    "notebook_path": str(notebook),
                    "input": {"target": address, "note": note},
                }
            )

            response = dispatch_tool_request(
                {
                    "protocol": "nollm.tool.v0.1",
                    "action": "nollm.read_card",
                    "notebook_path": str(notebook),
                    "input": {"target": address},
                }
            )

            self.assertTrue(response["ok"], response)
            self.assertNotIn(note, json.dumps(response))

    def assert_no_context_fields(self, result: dict) -> None:
        forbidden = {
            "neighbors",
            "related_cards",
            "shared_anchor_cards",
            "context",
            "recommendations",
            "ranked_cards",
            "semantic_matches",
        }
        self.assertTrue(forbidden.isdisjoint(result), result)


if __name__ == "__main__":
    unittest.main()
