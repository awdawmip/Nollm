from __future__ import annotations

import json
from pathlib import Path
import unittest

from nollm.dream_placement import placement_candidate_from_record
from nollm.dream_shard import shard_from_record


ROOT = Path(__file__).resolve().parents[3]
EXAMPLE_DIR = ROOT / "examples" / "openclaw_dream"
DOC = ROOT / "docs" / "experiments" / "D7_OPENCLAW_DREAM_EXPERIMENT.md"


class OpenClawDreamExperimentTests(unittest.TestCase):
    def test_fixtures_load_and_validate(self) -> None:
        shards = json.loads((EXAMPLE_DIR / "shards.json").read_text(encoding="utf-8"))
        placements = json.loads((EXAMPLE_DIR / "placements.json").read_text(encoding="utf-8"))

        parsed_shards = [shard_from_record(record) for record in shards]
        parsed_placements = [placement_candidate_from_record(record) for record in placements]

        self.assertEqual(len(parsed_shards), 2)
        self.assertEqual(len(parsed_placements), 2)
        self.assertEqual({item.shard_id for item in parsed_shards}, {item.shard_id for item in parsed_placements})

    def test_experiment_doc_warns_no_runtime_or_network(self) -> None:
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("offline fixture", text)
        self.assertIn("no network call", text)
        self.assertIn("no external", text)
        self.assertIn("no production placement", text)


if __name__ == "__main__":
    unittest.main()
