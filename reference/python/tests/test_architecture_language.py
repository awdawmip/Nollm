from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CURRENT_DOCS = [
    ROOT / "README.md",
    ROOT / "ARCHITECTURE.md",
    ROOT / "ROADMAP.md",
    ROOT / "AGENTS.md",
    ROOT / "docs" / "project" / "NOLLM_CURRENT_STATUS.md",
    ROOT / "docs" / "architecture" / "NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md",
]
HISTORICAL_DOCS = [
    ROOT / "protocol" / "v2" / "LAYER_CONSTITUTION.md",
    ROOT / "protocol" / "v2" / "LEGACY_BOUNDARY.md",
    ROOT / "docs" / "history" / "M0_SUPERSEDED_ROUTE_INDEX.md",
]


class ArchitectureLanguageTests(unittest.TestCase):
    def test_current_m0_architecture_language_is_present(self) -> None:
        corpus = "\n".join(path.read_text(encoding="utf-8") for path in CURRENT_DOCS)
        for phrase in [
            "Nollm is in the M0 modular-monorepo stage",
            "Architecture is the Index",
            "Core owns deterministic geometry current state",
            "Snapshot, Trace, Access, History, Audit, OpenClaw, Lab, and Distributions",
            "OpenClaw Live Integration",
            "GRF8 is an engineering checkpoint, not accepted architecture",
            "Evidence-first V2/V2.1/V2.2",
            "M1 is not started",
            "not been physically split on GitHub",
        ]:
            self.assertIn(phrase, corpus)
        self.assertIn("paused", corpus.lower())
        self.assertIn("historical or superseded", corpus.lower())

    def test_historical_v2_language_is_preserved_but_superseded(self) -> None:
        for path in HISTORICAL_DOCS:
            self.assertTrue(path.is_file(), path)
        historical = "\n".join(path.read_text(encoding="utf-8") for path in HISTORICAL_DOCS)
        self.assertIn("L0 Constitution and Protocol", historical)
        self.assertIn("not active architecture", historical)
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
