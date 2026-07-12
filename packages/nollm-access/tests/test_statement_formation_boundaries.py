from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FORMATION = ROOT / "packages/nollm-access/src/nollm_access/formation.py"
FORBIDDEN = {
    "embedding", "vector", "graph", "semantic_similarity", "keyword_score",
    "importance_score", "truth_score", "target_cell", "geometryaddress",
    "atomhandle", "bridgespec", "reuse", "revision", "stitch", "placement",
    "openclaw",
}


def test_formation_ast_has_no_semantic_or_geometry_surface() -> None:
    tree = ast.parse(FORMATION.read_text(encoding="utf-8"))
    names = {node.id.lower() for node in ast.walk(tree) if isinstance(node, ast.Name)}
    names |= {node.name.lower() for node in ast.walk(tree) if isinstance(node, (ast.ClassDef, ast.FunctionDef))}
    names |= {node.attr.lower() for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    imports = {alias.name.lower() for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
    imports |= {node.module.lower() for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
    assert not (names & FORBIDDEN)
    assert imports <= {"__future__", "dataclasses", "json", "typing", "statement"}


def test_core_snapshot_trace_do_not_import_formation() -> None:
    roots = [ROOT / "packages/nollm-core", ROOT / "packages/nollm-snapshot", ROOT / "packages/nollm-trace"]
    for package_root in roots:
        for path in package_root.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            imports = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
            imports |= {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
            assert not any(name == "nollm_access" or name.startswith("nollm_access.") for name in imports)
