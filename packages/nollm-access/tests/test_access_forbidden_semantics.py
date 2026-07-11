import ast
from pathlib import Path

import nollm_access


FORBIDDEN_API = {"infer_decision", "automatic_placement", "semantic_search", "find_similar", "hash_placement"}


def test_access_has_no_python_semantic_decision_surface() -> None:
    assert FORBIDDEN_API.isdisjoint(dir(nollm_access))
    root = Path(nollm_access.__file__).parent
    for path in root.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = {node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
        assert FORBIDDEN_API.isdisjoint(names)


def test_access_does_not_import_legacy_grf() -> None:
    root = Path(nollm_access.__file__).parent
    assert "nollm.grf" not in "\n".join(path.read_text(encoding="utf-8") for path in root.glob("*.py"))
