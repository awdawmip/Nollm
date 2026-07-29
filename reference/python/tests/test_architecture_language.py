from __future__ import annotations

import unittest
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CURRENT_DOCS = [
    ROOT / "README.md",
    ROOT / "ARCHITECTURE.md",
    ROOT / "ROADMAP.md",
    ROOT / "docs" / "project" / "ACTIVE_PROJECT.md",
    ROOT / "docs" / "project" / "NOLLM_PROJECT_BOOK_V3_1_CORE_PURITY_AND_EVOLVING_BASELINES_20260711.md",
    ROOT / "docs" / "project" / "NOLLM_CURRENT_STATUS.md",
    ROOT / "docs" / "architecture" / "NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md",
]
HISTORICAL_DOCS = [
    ROOT / "protocol" / "v2" / "LAYER_CONSTITUTION.md",
    ROOT / "protocol" / "v2" / "LEGACY_BOUNDARY.md",
    ROOT / "docs" / "history" / "M0_SUPERSEDED_ROUTE_INDEX.md",
]


class ArchitectureLanguageTests(unittest.TestCase):
    def test_active_v31_architecture_language_is_present(self) -> None:
        corpus = "\n".join(path.read_text(encoding="utf-8") for path in CURRENT_DOCS)
        for phrase in [
            "V3.1",
            "Architecture is the Index",
            "Core owns deterministic geometry current state",
            "explicit package ownership",
            "Private submodules are implementation details",
            "no baseline automatically starts another stage",
            "GRF8 is an engineering checkpoint, not accepted architecture",
            "Evidence-first V2/V2.1/V2.2",
            "M1 does not prove LLM placement quality",
            "active project basis",
        ]:
            self.assertIn(phrase, corpus)
        self.assertIn("historical or superseded", corpus.lower())

    def test_historical_v2_language_is_preserved_but_superseded(self) -> None:
        plan = json.loads((ROOT / "docs/architecture/module-ownership/ACTIVE_ASSET_CURATION_PLAN.json").read_text(encoding="utf-8"))
        by_path = {row["path"]: row for row in plan["assets"]}
        for path in HISTORICAL_DOCS:
            relative = path.relative_to(ROOT).as_posix()
            if relative.startswith("docs/history/"):
                self.assertFalse(path.exists(), path)
                self.assertEqual(by_path[relative]["classification"], "ARCHIVE_HISTORICAL")
            else:
                self.assertTrue(path.is_file(), path)
        current = "\n".join(path.read_text(encoding="utf-8") for path in CURRENT_DOCS)
        self.assertNotIn("V2 is the only active architecture", current)

    def test_docs_do_not_introduce_forbidden_runtime_dependencies(self) -> None:
        corpus = "\n".join(path.read_text(encoding="utf-8").lower() for path in CURRENT_DOCS)
        forbidden_imports = [
            "import sqlite3",
            "import openai",
            "import requests",
            "import httpx",
            "chromadb",
            "faiss",
            "networkx",
            "sentence_transformers",
        ]
        for phrase in forbidden_imports:
            self.assertNotIn(phrase, corpus)


if __name__ == "__main__":
    unittest.main()
