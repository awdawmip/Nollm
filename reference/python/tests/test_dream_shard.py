from __future__ import annotations

import ast
from pathlib import Path
import unittest

from nollm.dream_shard import (
    DreamShard,
    is_independently_meaningful,
    normalize_shard_text,
    shard_from_record,
    shard_to_record,
)


ROOT = Path(__file__).resolve().parents[3]
DREAM_SHARD_SOURCE = ROOT / "reference" / "python" / "nollm" / "dream_shard.py"


class DreamShardTests(unittest.TestCase):
    def test_normalization_strips_and_collapses_whitespace(self) -> None:
        self.assertEqual(
            normalize_shard_text("  Nollm\tkeeps\nsmall   residues.  "),
            "Nollm keeps small residues.",
        )

    def test_valid_shard_accepts_meaningful_utterance(self) -> None:
        shard = DreamShard(
            shard_id="shard-1",
            text="  Geometry remains pre-card material. ",
            source="project_note",
            anchors_hint=("geometry",),
            metadata={"speaker": "codex"},
        )
        self.assertEqual(shard.text, "Geometry remains pre-card material.")
        self.assertEqual(shard.status, "candidate")

    def test_empty_or_punctuation_only_shard_is_rejected(self) -> None:
        for text in ("", "   ", "!!! ???"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    DreamShard(shard_id="bad", text=text)
                self.assertFalse(is_independently_meaningful(text))

    def test_too_short_shard_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            DreamShard(shard_id="short", text="short")

    def test_confirmed_status_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            DreamShard(shard_id="status", text="This shard is meaningful.", status="confirmed")

    def test_unknown_source_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            DreamShard(shard_id="source", text="This shard is meaningful.", source="llm_inference")

    def test_empty_anchor_hint_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            DreamShard(
                shard_id="anchor",
                text="This shard is meaningful.",
                anchors_hint=("geometry", ""),
            )

    def test_non_string_metadata_key_or_value_is_rejected(self) -> None:
        invalid_metadata = [{1: "value"}, {"key": 1}]
        for metadata in invalid_metadata:
            with self.subTest(metadata=metadata):
                with self.assertRaises(ValueError):
                    DreamShard(
                        shard_id="metadata",
                        text="This shard is meaningful.",
                        metadata=metadata,  # type: ignore[arg-type]
                    )

    def test_shard_record_roundtrip(self) -> None:
        shard = DreamShard(
            shard_id="roundtrip",
            text="Dream shards remain pre-card material.",
            source="assistant_utterance",
            status="draft",
            anchors_hint=("dream-geometry", "d3"),
            metadata={"thread": "minimal"},
        )
        record = shard_to_record(shard)
        self.assertEqual(record["anchors_hint"], ["dream-geometry", "d3"])
        self.assertEqual(shard_from_record(record), shard)

    def test_module_does_not_import_forbidden_runtime_layers(self) -> None:
        tree = ast.parse(DREAM_SHARD_SOURCE.read_text(encoding="utf-8"))
        imported_modules: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module.split(".")[0])

        forbidden = {
            "annotation",
            "audit",
            "chart_gluing",
            "cli",
            "filesystem",
            "geometry",
            "history",
            "honeycomb",
            "models",
            "recall",
            "review",
            "tool_api",
            "validation",
        }
        self.assertTrue(imported_modules.isdisjoint(forbidden))


if __name__ == "__main__":
    unittest.main()
