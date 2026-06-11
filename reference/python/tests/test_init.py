from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from nollm.cli import main
from nollm.models import CARD_DIRS


class InitTests(unittest.TestCase):
    def test_init_creates_expected_structure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = Path(tmp) / "nb"
            self.assertEqual(main(["init", str(notebook), "--notebook", "demo"]), 0)
            self.assertTrue((notebook / "anchors.yaml").exists())
            self.assertTrue((notebook / "aliases.yaml").exists())
            self.assertTrue((notebook / "ledger" / "events.jsonl").exists())
            self.assertTrue((notebook / "recalls").is_dir())
            for directory in CARD_DIRS.values():
                self.assertTrue((notebook / "cards" / directory).is_dir())


if __name__ == "__main__":
    unittest.main()

