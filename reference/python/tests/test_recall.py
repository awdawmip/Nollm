from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from nollm.cli import main
from nollm.models import RECALL_KEYS
from test_write_read import init_notebook, write_card


class RecallTests(unittest.TestCase):
    def test_recall_returns_json_digest_with_required_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            write_card(notebook, title="Filesystem Memory")
            self.assertEqual(main(["recall", str(notebook), "filesystem memory"]), 0)
            digests = list((notebook / "recalls").glob("*.json"))
            self.assertEqual(len(digests), 1)
            digest = json.loads(digests[0].read_text(encoding="utf-8"))
            for key in RECALL_KEYS:
                self.assertIn(key, digest)

    def test_recall_prefers_confirmed_over_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            candidate_address, _event_id = write_card(notebook, title="Memory Candidate")
            confirmed_address, _event_id = write_card(notebook, title="Memory Confirmed")
            self.assertEqual(
                main(
                    [
                        "status",
                        str(notebook),
                        confirmed_address,
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
            self.assertEqual(main(["recall", str(notebook), "memory"]), 0)
            digest_path = sorted((notebook / "recalls").glob("*.json"))[-1]
            digest = json.loads(digest_path.read_text(encoding="utf-8"))
            self.assertEqual(digest["cards_read"][0], confirmed_address)
            self.assertIn(candidate_address, digest["cards_read"])
            self.assertTrue(digest["warnings"])


if __name__ == "__main__":
    unittest.main()

