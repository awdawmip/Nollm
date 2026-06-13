from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from nollm.cortex import focus_cards
from nollm.filesystem import read_card, write_card_file
from nollm.tool_api import dispatch_tool_request
from nollm.validation import validate_notebook
from test_write_read import init_notebook, write_card


ROOT = Path(__file__).resolve().parents[3]


def valid_metadata() -> dict:
    return {
        "layer": 1,
        "hex": {"q": 0, "r": 0, "rotation": 22.5, "scale": 0.8408964153},
        "anchor_fields": {"architecture_is_index": {"weight": 0.9, "role": "primary"}},
        "scale_links": {"coarser": [], "finer": [], "overlaps": [], "recovery": []},
    }


def write_card_with_metadata(notebook: Path, metadata: dict) -> str:
    address, _event_id = write_card(notebook, title="Honeycomb Metadata")
    card_id = address.rsplit("/", 1)[-1]
    front, body, card_path = read_card(notebook, card_id)
    front.update(metadata)
    write_card_file(card_path, front, body)
    return card_id


class HoneycombMetadataTests(unittest.TestCase):
    def test_valid_metadata_round_trips_and_validates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            card_id = write_card_with_metadata(notebook, valid_metadata())

            self.assertEqual(validate_notebook(notebook), [])
            front, _body, _card_path = read_card(notebook, card_id)
            self.assertEqual(front["layer"], 1)
            self.assertEqual(front["hex"]["rotation"], 22.5)
            self.assertEqual(front["anchor_fields"]["architecture_is_index"]["role"], "primary")
            self.assertEqual(front["scale_links"]["coarser"], [])

    def test_focus_includes_compact_metadata_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            write_card_with_metadata(notebook, valid_metadata())

            result = focus_cards(notebook, anchor_id="project:demo")
            card = result["cards"][0]
            self.assertEqual(card["layer"], 1)
            self.assertIn("architecture_is_index", card["anchor_fields"])
            self.assertEqual(card["scale_links"]["coarser"], 0)

    def test_card_without_honeycomb_metadata_remains_valid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            write_card(notebook, title="Plain Card")

            self.assertEqual(validate_notebook(notebook), [])

    def test_invalid_negative_layer_fails_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            metadata = valid_metadata()
            metadata["layer"] = -1
            write_card_with_metadata(notebook, metadata)

            self.assertIssueContains(notebook, "layer must be a non-negative integer")

    def test_invalid_float_layer_fails_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            metadata = valid_metadata()
            metadata["layer"] = 1.5
            write_card_with_metadata(notebook, metadata)

            self.assertIssueContains(notebook, "layer must be a non-negative integer")

    def test_hex_without_q_or_r_fails_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            metadata = valid_metadata()
            metadata["hex"] = {"q": 0, "rotation": 22.5, "scale": 0.8408964153}
            write_card_with_metadata(notebook, metadata)

            self.assertIssueContains(notebook, "hex.r is required")

    def test_invalid_string_layer_fails_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            metadata = valid_metadata()
            metadata["layer"] = "two"
            write_card_with_metadata(notebook, metadata)

            self.assertIssueContains(notebook, "layer must be a non-negative integer")

    def test_invalid_hex_q_or_r_type_fails_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            metadata = valid_metadata()
            metadata["hex"] = {"q": "zero", "r": 0, "rotation": 22.5, "scale": 0.8408964153}
            write_card_with_metadata(notebook, metadata)

            self.assertIssueContains(notebook, "hex.q must be an integer")

    def test_rotation_without_layer_fails_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            metadata = valid_metadata()
            metadata.pop("layer")
            write_card_with_metadata(notebook, metadata)

            self.assertIssueContains(notebook, "hex.rotation requires a valid layer")

    def test_scale_without_layer_fails_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            metadata = valid_metadata()
            metadata.pop("layer")
            metadata["hex"].pop("rotation")
            write_card_with_metadata(notebook, metadata)

            self.assertIssueContains(notebook, "hex.scale requires a valid layer")

    def test_rotation_mismatch_fails_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            metadata = valid_metadata()
            metadata["hex"] = {"q": 0, "r": 0, "rotation": 45.0, "scale": 0.8408964153}
            write_card_with_metadata(notebook, metadata)

            self.assertIssueContains(notebook, "hex.rotation does not match layer rotation")

    def test_invalid_hex_scale_fails_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            metadata = valid_metadata()
            metadata["hex"] = {"q": 0, "r": 0, "rotation": 22.5, "scale": 0}
            write_card_with_metadata(notebook, metadata)

            self.assertIssueContains(notebook, "hex.scale must be a positive number")

    def test_scale_mismatch_fails_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            metadata = valid_metadata()
            metadata["hex"] = {"q": 0, "r": 0, "rotation": 22.5, "scale": 1.0}
            write_card_with_metadata(notebook, metadata)

            self.assertIssueContains(notebook, "hex.scale does not match layer scale")

    def test_invalid_anchor_field_weight_fails_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            metadata = valid_metadata()
            metadata["anchor_fields"] = {"architecture_is_index": {"weight": -0.1, "role": "primary"}}
            write_card_with_metadata(notebook, metadata)

            self.assertIssueContains(notebook, "anchor_fields weight out of range")

    def test_anchor_field_weight_above_one_fails_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            metadata = valid_metadata()
            metadata["anchor_fields"] = {"architecture_is_index": {"weight": 1.2, "role": "primary"}}
            write_card_with_metadata(notebook, metadata)

            self.assertIssueContains(notebook, "anchor_fields weight out of range")

    def test_anchor_field_missing_weight_fails_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            metadata = valid_metadata()
            metadata["anchor_fields"] = {"architecture_is_index": {"role": "primary"}}
            write_card_with_metadata(notebook, metadata)

            self.assertIssueContains(notebook, "anchor_fields weight is required")

    def test_invalid_anchor_field_role_fails_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            metadata = valid_metadata()
            metadata["anchor_fields"] = {"architecture_is_index": {"weight": 0.5, "role": "children"}}
            write_card_with_metadata(notebook, metadata)

            self.assertIssueContains(notebook, "anchor_fields has invalid role")

    def test_unregistered_anchor_field_key_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            metadata = valid_metadata()
            metadata["anchor_fields"] = {"not_in_anchor_registry": {"weight": 0.5, "role": "warning"}}
            write_card_with_metadata(notebook, metadata)

            self.assertEqual(validate_notebook(notebook), [])

    def test_invalid_scale_link_key_fails_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            metadata = valid_metadata()
            metadata["scale_links"] = {"children": []}
            write_card_with_metadata(notebook, metadata)

            self.assertIssueContains(notebook, "scale_links has invalid key")

    def test_invalid_scale_link_parent_key_fails_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            metadata = valid_metadata()
            metadata["scale_links"] = {"parent": []}
            write_card_with_metadata(notebook, metadata)

            self.assertIssueContains(notebook, "scale_links has invalid key")

    def test_empty_scale_link_value_fails_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            metadata = valid_metadata()
            metadata["scale_links"] = {"coarser": [""]}
            write_card_with_metadata(notebook, metadata)

            self.assertIssueContains(notebook, "scale_links value must be a card id or address")

    def test_json_tool_write_card_preserves_architecture_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            response = dispatch_tool_request(
                {
                    "protocol": "nollm.tool.v0.1",
                    "action": "nollm.write_card",
                    "notebook_path": str(notebook),
                    "input": {
                        "type": "fact",
                        "title": "Tool Honeycomb Metadata",
                        "claim": "Tool bridge preserves architecture metadata.",
                        "reason": "P5.1 preservation test.",
                        "anchors": ["project:demo"],
                        "source": "user_statement",
                        "trust": "unverified",
                        **valid_metadata(),
                    },
                }
            )

            self.assertTrue(response["ok"])
            front, _body, _path = read_card(notebook, response["result"]["address"])
            self.assertEqual(front["layer"], 1)
            self.assertEqual(front["hex"]["scale"], 0.8408964153)
            self.assertEqual(front["anchor_fields"]["architecture_is_index"]["weight"], 0.9)
            self.assertEqual(front["scale_links"]["recovery"], [])

    def test_example_openclaw_notebook_validates(self) -> None:
        self.assertEqual(validate_notebook(ROOT / "examples" / "openclaw"), [])

    def assertIssueContains(self, notebook: Path, expected: str) -> None:
        issues = validate_notebook(notebook)
        self.assertTrue(any(expected in issue for issue in issues), issues)


if __name__ == "__main__":
    unittest.main()
