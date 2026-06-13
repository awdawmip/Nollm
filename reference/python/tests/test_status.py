from __future__ import annotations

import tempfile
import unittest
from contextlib import redirect_stderr
import io

from nollm.cli import main
from nollm.filesystem import read_card
from nollm.validation import validate_notebook
from test_write_read import init_notebook, write_card


class StatusTests(unittest.TestCase):
    def test_status_to_confirmed_requires_human_approval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            address, _event_id = write_card(notebook)
            code = main(["status", str(notebook), address, "--to", "confirmed", "--reason", "reviewed"])
            self.assertNotEqual(code, 0)

    def test_status_appends_ledger_event(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            address, _event_id = write_card(notebook)
            before = (notebook / "ledger" / "events.jsonl").read_text(encoding="utf-8").count("\n")
            code = main(
                [
                    "status",
                    str(notebook),
                    address,
                    "--to",
                    "confirmed",
                    "--reason",
                    "reviewed",
                    "--human-approval",
                    "approved by test",
                ]
            )
            self.assertEqual(code, 0)
            ledger = (notebook / "ledger" / "events.jsonl").read_text(encoding="utf-8")
            self.assertEqual(ledger.count("\n"), before + 1)
            self.assertIn('"op":"update_status"', ledger)
            self.assertIn('"to_status":"confirmed"', ledger)
            self.assertIn('"trust_before":"unverified"', ledger)
            self.assertIn('"trust_after":"human-approved"', ledger)

            front, _body, _path = read_card(notebook, address)
            self.assertEqual(front["trust"], "human-approved")
            self.assertEqual(validate_notebook(notebook), [])

    def test_confirm_rejects_llm_inference_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            address, _event_id = write_card(notebook, source="llm_inference", trust="llm-proposed")
            error = io.StringIO()
            with redirect_stderr(error):
                code = main(
                    [
                        "status",
                        str(notebook),
                        address,
                        "--to",
                        "confirmed",
                        "--reason",
                        "reviewed",
                        "--human-approval",
                        "approved by test",
                    ]
                )
            self.assertNotEqual(code, 0)
            self.assertIn("cannot confirm", error.getvalue())

    def test_invalid_status_transition_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            address, _event_id = write_card(notebook)
            error = io.StringIO()
            with redirect_stderr(error):
                code = main(["status", str(notebook), address, "--to", "draft", "--reason", "backtrack"])
            self.assertNotEqual(code, 0)
            self.assertIn("invalid status transition", error.getvalue())

    def test_superseded_requires_existing_target_card(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            address, _event_id = write_card(notebook)
            main(
                [
                    "status",
                    str(notebook),
                    address,
                    "--to",
                    "confirmed",
                    "--reason",
                    "reviewed",
                    "--human-approval",
                    "approved by test",
                ]
            )
            error = io.StringIO()
            with redirect_stderr(error):
                code = main(
                    [
                        "status",
                        str(notebook),
                        address,
                        "--to",
                        "superseded",
                        "--reason",
                        "replaced",
                        "--superseded-by",
                        "card_missing",
                    ]
                )
            self.assertNotEqual(code, 0)
            self.assertIn("must resolve to an existing card", error.getvalue())

    def test_superseded_rejects_self_supersede(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            address, _event_id = write_card(notebook)
            main(
                [
                    "status",
                    str(notebook),
                    address,
                    "--to",
                    "confirmed",
                    "--reason",
                    "reviewed",
                    "--human-approval",
                    "approved by test",
                ]
            )
            error = io.StringIO()
            with redirect_stderr(error):
                code = main(
                    [
                        "status",
                        str(notebook),
                        address,
                        "--to",
                        "superseded",
                        "--reason",
                        "replaced",
                        "--superseded-by",
                        address,
                    ]
                )
            self.assertNotEqual(code, 0)
            self.assertIn("must not refer to the same card", error.getvalue())

    def test_allowed_status_transitions_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            draft, _event_id = write_card(notebook, title="Draft Card", status="draft")
            replacement, _event_id = write_card(notebook, title="Replacement Card")

            self.assertEqual(main(["status", str(notebook), draft, "--to", "candidate", "--reason", "ready"]), 0)
            self.assertEqual(
                main(
                    [
                        "status",
                        str(notebook),
                        draft,
                        "--to",
                        "confirmed",
                        "--reason",
                        "reviewed",
                        "--human-approval",
                        "approved by test",
                    ]
                ),
                0,
            )
            self.assertEqual(
                main(
                    [
                        "status",
                        str(notebook),
                        draft,
                        "--to",
                        "superseded",
                        "--reason",
                        "replaced",
                        "--superseded-by",
                        replacement,
                    ]
                ),
                0,
            )
            self.assertEqual(main(["status", str(notebook), draft, "--to", "archived", "--reason", "old"]), 0)


if __name__ == "__main__":
    unittest.main()
