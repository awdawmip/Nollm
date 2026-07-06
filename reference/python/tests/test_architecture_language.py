from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DOCS = [
    ROOT / "README.md",
    ROOT / "ARCHITECTURE.md",
    ROOT / "ROADMAP.md",
    ROOT / "AGENTS.md",
    ROOT / "protocol" / "v2" / "LAYER_CONSTITUTION.md",
    ROOT / "protocol" / "v2" / "LEGACY_BOUNDARY.md",
]


class ArchitectureLanguageTests(unittest.TestCase):
    def test_required_architecture_phrases_are_present(self) -> None:
        corpus = "\n".join(path.read_text(encoding="utf-8") for path in DOCS)
        for phrase in [
            "V2 is the only active architecture",
            "L6 -> L5 -> L4 -> L3 -> L2 -> L1 -> L0",
            "Core does not import adapters or terminals",
            "Adapters translate",
            "Terminals present",
            "OpenClaw legacy is a frozen L5/L6 migration asset",
        ]:
            self.assertIn(phrase, corpus)

    def test_docs_do_not_introduce_forbidden_runtime_dependencies(self) -> None:
        corpus = "\n".join(path.read_text(encoding="utf-8").lower() for path in DOCS)
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
