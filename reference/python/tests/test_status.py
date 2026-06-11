from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from nollm.cli import main
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


if __name__ == "__main__":
    unittest.main()

