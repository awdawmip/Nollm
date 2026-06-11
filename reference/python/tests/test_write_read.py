from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from nollm.cli import main


def init_notebook(tmp: str) -> Path:
    notebook = Path(tmp) / "nb"
    main(["init", str(notebook), "--notebook", "demo"])
    return notebook


def write_card(notebook: Path, title: str = "A Fact", status: str = "candidate") -> tuple[str, str]:
    output = io.StringIO()
    with redirect_stdout(output):
        code = main(
            [
                "write",
                str(notebook),
                "--type",
                "fact",
                "--title",
                title,
                "--claim",
                "Nollm stores memory in files.",
                "--reason",
                "Test write.",
                "--anchor",
                "project:demo",
                "--source",
                "user_statement",
                "--trust",
                "unverified",
                "--status",
                status,
                "--body",
                "Body mentions Nollm and files.",
            ]
        )
    self_output = output.getvalue().strip().splitlines()
    assert code == 0
    return self_output[0], self_output[1]


class WriteReadTests(unittest.TestCase):
    def test_write_creates_card_and_ledger_event(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            address, event_id = write_card(notebook)
            card_id = address.rsplit("/", 1)[-1]
            self.assertTrue(list((notebook / "cards").rglob(f"{card_id}.md")))
            ledger = (notebook / "ledger" / "events.jsonl").read_text(encoding="utf-8")
            self.assertIn(event_id, ledger)
            self.assertIn('"op":"write_card"', ledger)

    def test_write_refuses_confirmed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            code = main(
                [
                    "write",
                    str(notebook),
                    "--type",
                    "fact",
                    "--title",
                    "No Confirmed Write",
                    "--claim",
                    "x",
                    "--reason",
                    "x",
                    "--anchor",
                    "project:demo",
                    "--source",
                    "user_statement",
                    "--trust",
                    "unverified",
                    "--status",
                    "confirmed",
                ]
            )
            self.assertNotEqual(code, 0)

    def test_read_resolves_card_id_and_memory_address(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            address, _event_id = write_card(notebook)
            card_id = address.rsplit("/", 1)[-1]
            for target in [card_id, address]:
                output = io.StringIO()
                with redirect_stdout(output):
                    self.assertEqual(main(["read", str(notebook), target]), 0)
                self.assertIn("Nollm stores memory in files.", output.getvalue())


if __name__ == "__main__":
    unittest.main()

