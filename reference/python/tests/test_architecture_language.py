from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DOCS = [
    ROOT / "README.md",
    ROOT / "ARCHITECTURE.md",
    ROOT / "protocol" / "HONEYCOMB_FIELD.md",
    ROOT / "protocol" / "ANCHOR_FIELD.md",
    ROOT / "protocol" / "SCALE_SCAN.md",
    ROOT / "cortex" / "CORTEX_PROMPT.md",
]


class ArchitectureLanguageTests(unittest.TestCase):
    def test_required_architecture_phrases_are_present(self) -> None:
        corpus = "\n".join(path.read_text(encoding="utf-8") for path in DOCS)
        for phrase in [
            "Anchor is Field, not Folder",
            "Recall is Scale Scan, not Tree Descent",
            "SQLite is Audit Projection",
            "Layered rotating honeycomb memory field",
            "22.5",
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
