from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ForbiddenFeatureTests(unittest.TestCase):
    def test_no_prohibited_dependency_or_feature_is_introduced(self) -> None:
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn("dependencies = []", pyproject)

        forbidden = {
            "sqlite3",
            "openai",
            "requests",
            "httpx",
            "numpy",
            "sklearn",
            "networkx",
            "chromadb",
            "faiss",
            "sentence_transformers",
        }
        for path in (ROOT / "nollm").glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = {alias.name.split(".")[0] for alias in node.names}
                    self.assertFalse(names & forbidden, f"forbidden import in {path}: {names & forbidden}")
                if isinstance(node, ast.ImportFrom) and node.module:
                    name = node.module.split(".")[0]
                    self.assertNotIn(name, forbidden, f"forbidden import in {path}: {name}")


if __name__ == "__main__":
    unittest.main()

