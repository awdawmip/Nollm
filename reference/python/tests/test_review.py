from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from nollm.cli import main
from nollm.filesystem import read_ledger


def run_json(args: list[str]) -> dict:
    output = io.StringIO()
    with redirect_stdout(output):
        code = main(args)
    assert code == 0
    return json.loads(output.getvalue())


def init_notebook(tmp: str) -> Path:
    notebook = Path(tmp) / "nb"
    assert main(["init", str(notebook), "--notebook", "demo"]) == 0
    return notebook


def write_card(
    notebook: Path,
    *,
    title: str,
    card_type: str = "fact",
    status: str = "candidate",
    trust: str = "unverified",
    source: str = "user_statement",
    body: str = "Full body should not appear in review output.",
) -> str:
    output = io.StringIO()
    with redirect_stdout(output):
        code = main(
            [
                "write",
                str(notebook),
                "--type",
                card_type,
                "--title",
                title,
                "--claim",
                f"{title} claim.",
                "--reason",
                "Review test.",
                "--anchor",
                "project:demo",
                "--source",
                source,
                "--trust",
                trust,
                "--status",
                status,
                "--body",
                body,
            ]
        )
    assert code == 0
    return output.getvalue().splitlines()[0]


def confirm_card(notebook: Path, address: str) -> None:
    output = io.StringIO()
    with redirect_stdout(output):
        code = main(
            [
                "status",
                str(notebook),
                address,
                "--to",
                "confirmed",
                "--reason",
                "Human reviewed.",
                "--human-approval",
                "Approved by test.",
            ]
        )
    assert code == 0


class ReviewTests(unittest.TestCase):
    def test_default_review_includes_candidate_and_draft_but_excludes_confirmed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            write_card(notebook, title="Draft Card", status="draft")
            write_card(notebook, title="Candidate Card", status="candidate")
            confirmed = write_card(notebook, title="Confirmed Card", status="candidate")
            confirm_card(notebook, confirmed)

            review = run_json(["review", str(notebook)])

            self.assertTrue(review["ok"])
            self.assertEqual(review["review_filters"]["statuses"], ["candidate", "draft"])
            titles = [card["title"] for card in review["cards"]]
            self.assertEqual(titles, ["Draft Card", "Candidate Card"])
            self.assertNotIn("Confirmed Card", titles)
            self.assertEqual(review["review_count"], 2)

    def test_review_status_filter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            write_card(notebook, title="Draft Card", status="draft")
            write_card(notebook, title="Candidate Card", status="candidate")

            review = run_json(["review", str(notebook), "--status", "candidate"])

            self.assertEqual([card["title"] for card in review["cards"]], ["Candidate Card"])
            self.assertEqual(review["review_filters"]["statuses"], ["candidate"])

    def test_inspect_alias_uses_review_filters(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            write_card(notebook, title="Fact Card", card_type="fact")
            write_card(notebook, title="Decision Card", card_type="decision", trust="llm-proposed")

            inspection = run_json(
                [
                    "inspect",
                    str(notebook),
                    "--status",
                    "candidate",
                    "--type",
                    "decision",
                    "--anchor",
                    "project:demo",
                    "--trust",
                    "llm-proposed",
                    "--limit",
                    "20",
                ]
            )

            self.assertTrue(inspection["ok"])
            self.assertEqual(inspection["review_count"], 1)
            self.assertEqual(inspection["cards"][0]["title"], "Decision Card")
            self.assertNotIn("body", inspection["cards"][0])
            self.assertEqual(inspection["review_filters"]["statuses"], ["candidate"])
            self.assertEqual(inspection["review_filters"]["type"], "decision")
            self.assertEqual(inspection["review_filters"]["anchor"], "project:demo")
            self.assertEqual(inspection["review_filters"]["trust"], "llm-proposed")

    def test_review_type_filter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            write_card(notebook, title="Fact Card", card_type="fact")
            write_card(notebook, title="Decision Card", card_type="decision")

            review = run_json(["review", str(notebook), "--type", "decision"])

            self.assertEqual([card["title"] for card in review["cards"]], ["Decision Card"])
            self.assertEqual(review["cards"][0]["type"], "decision")

    def test_review_anchor_and_trust_filters(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            write_card(notebook, title="Unverified Card", trust="unverified")
            write_card(notebook, title="Proposed Card", trust="llm-proposed")

            review = run_json(["review", str(notebook), "--anchor", "project:demo", "--trust", "llm-proposed"])

            self.assertEqual([card["title"] for card in review["cards"]], ["Proposed Card"])
            self.assertEqual(review["review_filters"]["anchor"], "project:demo")
            self.assertEqual(review["review_filters"]["trust"], "llm-proposed")

    def test_review_limit_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            write_card(notebook, title="Candidate B", status="candidate")
            write_card(notebook, title="Draft A", status="draft")
            write_card(notebook, title="Candidate A", status="candidate")

            first = run_json(["review", str(notebook), "--limit", "2"])
            second = run_json(["review", str(notebook), "--limit", "2"])

            self.assertEqual(first, second)
            self.assertEqual(first["review_count"], 2)
            self.assertEqual(first["cards"][0]["status"], "draft")

    def test_review_output_excludes_body_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            write_card(notebook, title="Body Card", body="Secret body text.")

            review = run_json(["review", str(notebook)])

            self.assertNotIn("body", review["cards"][0])
            self.assertNotIn("Secret body text.", json.dumps(review))

    def test_review_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            write_card(notebook, title="Read Only Card")
            ledger_before = read_ledger(notebook)
            files_before = sorted(path.relative_to(notebook).as_posix() for path in notebook.rglob("*") if path.is_file())

            review = run_json(["review", str(notebook)])

            self.assertTrue(review["ok"])
            self.assertEqual(read_ledger(notebook), ledger_before)
            files_after = sorted(path.relative_to(notebook).as_posix() for path in notebook.rglob("*") if path.is_file())
            self.assertEqual(files_after, files_before)
            self.assertEqual(list((notebook / "recalls").glob("recall_*")), [])
            self.assertEqual(list(notebook.glob("*audit*")), [])

    def test_inspect_alias_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            write_card(notebook, title="Read Only Inspect Card")
            ledger_before = read_ledger(notebook)
            files_before = sorted(path.relative_to(notebook).as_posix() for path in notebook.rglob("*") if path.is_file())

            inspection = run_json(["inspect", str(notebook)])

            self.assertTrue(inspection["ok"])
            self.assertEqual(read_ledger(notebook), ledger_before)
            files_after = sorted(path.relative_to(notebook).as_posix() for path in notebook.rglob("*") if path.is_file())
            self.assertEqual(files_after, files_before)


if __name__ == "__main__":
    unittest.main()
