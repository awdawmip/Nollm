from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from nollm.validation import validate_notebook
from test_write_read import init_notebook, write_card


ROOT = Path(__file__).resolve().parents[3]


def write_digest(notebook: Path, digest: dict) -> None:
    recalls = notebook / "recalls"
    recalls.mkdir(exist_ok=True)
    (recalls / "recall_0001.json").write_text(json.dumps(digest, ensure_ascii=False), encoding="utf-8")


def valid_digest(card_address: str) -> dict:
    return {
        "query_or_task": "recall metadata",
        "memory_intent": "recall_focus",
        "anchors_used": ["project:demo"],
        "cards_read": [card_address],
        "recalled_points": ["Nollm stores memory in files."],
        "warnings": [],
        "do_not_assume": [],
        "source_addresses": [card_address],
        "open_questions": [],
        "active_anchor_fields": ["architecture_is_index"],
        "scale_path": [
            {
                "layer": 1,
                "card": card_address,
                "anchor_fields": ["architecture_is_index"],
                "note": "metadata-only",
            }
        ],
        "lateral_recovery": [],
        "sufficient_scale_reached": True,
    }


class RecallDigestValidationTests(unittest.TestCase):
    def test_valid_sample_openclaw_recall_digest_passes_validation(self) -> None:
        self.assertEqual(validate_notebook(ROOT / "examples" / "openclaw"), [])

    def test_valid_recall_digest_passes_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            card_address, _event_id = write_card(notebook)
            write_digest(notebook, valid_digest(card_address))

            self.assertEqual(validate_notebook(notebook), [])

    def test_missing_scale_scan_recall_digest_fields_fail_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            card_address, _event_id = write_card(notebook)
            digest = valid_digest(card_address)
            digest.pop("active_anchor_fields")
            write_digest(notebook, digest)

            self.assertIssueContains(notebook, "recall digest missing key", "active_anchor_fields")

    def test_invalid_memory_intent_fails_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            card_address, _event_id = write_card(notebook)
            digest = valid_digest(card_address)
            digest["memory_intent"] = "focus"
            write_digest(notebook, digest)

            self.assertIssueContains(notebook, "invalid memory_intent", "focus")

    def test_invalid_sufficient_scale_reached_type_fails_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            card_address, _event_id = write_card(notebook)
            digest = valid_digest(card_address)
            digest["sufficient_scale_reached"] = "yes"
            write_digest(notebook, digest)

            self.assertIssueContains(notebook, "sufficient_scale_reached must be a boolean")

    def test_invalid_active_anchor_fields_item_fails_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            card_address, _event_id = write_card(notebook)
            digest = valid_digest(card_address)
            digest["active_anchor_fields"] = [1]
            write_digest(notebook, digest)

            self.assertIssueContains(notebook, "active_anchor_fields must contain strings")

    def test_invalid_scale_path_negative_layer_fails_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            card_address, _event_id = write_card(notebook)
            digest = valid_digest(card_address)
            digest["scale_path"][0]["layer"] = -1
            write_digest(notebook, digest)

            self.assertIssueContains(notebook, "scale_path layer must be a non-negative integer")

    def assertIssueContains(self, notebook: Path, *expected_parts: str) -> None:
        issues = validate_notebook(notebook)
        self.assertTrue(
            any(all(part in issue for part in expected_parts) for issue in issues),
            issues,
        )


if __name__ == "__main__":
    unittest.main()
