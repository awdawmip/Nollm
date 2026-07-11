import ast
from pathlib import Path
import sys


SOURCE = Path(__file__).resolve().parents[1] / "src" / "nollm_core"
STDLIB = set(sys.stdlib_module_names)


def test_core_imports_only_stdlib_and_relative_modules() -> None:
    external = set()
    for path in SOURCE.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                external.update(alias.name.split(".")[0] for alias in node.names if alias.name.split(".")[0] not in STDLIB)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                name = node.module.split(".")[0]
                if name not in STDLIB:
                    external.add(name)
    assert external == set()
