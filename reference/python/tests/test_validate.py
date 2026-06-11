from __future__ import annotations

import tempfile
import unittest

from nollm.cli import main
from nollm.filesystem import read_card, write_card_file
from nollm.validation import validate_notebook
from test_write_read import init_notebook, write_card


class ValidateTests(unittest.TestCase):
    def test_validate_passes_after_init_and_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            write_card(notebook)
            self.assertEqual(validate_notebook(notebook), [])
            self.assertEqual(main(["validate", str(notebook)]), 0)

    def test_validate_fails_on_unknown_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            address, _event_id = write_card(notebook)
            front, body, card_path = read_card(notebook, address)
            front["anchors"] = ["project:missing"]
            write_card_file(card_path, front, body)
            issues = validate_notebook(notebook)
            self.assertTrue(any("unknown anchor" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()

