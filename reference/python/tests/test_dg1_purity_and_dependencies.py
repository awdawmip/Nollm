import ast
import importlib
import pathlib


REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
GEOMETRY_ROOT = REPO_ROOT / "reference" / "python" / "nollm" / "dream_geometry" / "geometry"
VALIDATION_ROOT = REPO_ROOT / "reference" / "python" / "nollm" / "dream_geometry" / "validation"
FORBIDDEN_IMPORT_PREFIXES = (
    "nollm.geometry",
    "nollm.coverage",
    "nollm.chart_gluing",
    "nollm.openclaw_",
    "nollm.native_field",
    "nollm.dream_geometry.field",
    "nollm.dream_geometry.cortex",
    "nollm.dream_geometry.recall",
    "nollm.dream_geometry.adapters",
    "subprocess",
    "socket",
    "requests",
    "urllib",
)
FORBIDDEN_PUBLIC_FIELDS = {"anchor", "children", "folder", "semantic_search"}


def test_dg1_bd_01_geometry_and_validation_import_without_side_effects() -> None:
    for module in (
        "nollm.dream_geometry.geometry",
        "nollm.dream_geometry.geometry.types",
        "nollm.dream_geometry.geometry.hexgrid",
        "nollm.dream_geometry.geometry.chart",
        "nollm.dream_geometry.geometry.polygon",
        "nollm.dream_geometry.geometry.transform",
        "nollm.dream_geometry.geometry.coverage",
        "nollm.dream_geometry.geometry.metrics",
        "nollm.dream_geometry.geometry.schedules",
        "nollm.dream_geometry.validation",
    ):
        imported = importlib.import_module(module)
        assert imported.__all__ is not None


def test_dg1_bd_02_geometry_does_not_import_forbidden_modules() -> None:
    for path in GEOMETRY_ROOT.rglob("*.py"):
        imports = _imports(path)
        for imported in imports:
            assert not imported.startswith(FORBIDDEN_IMPORT_PREFIXES), f"{path} imports {imported}"


def test_dg1_bd_03_production_modules_do_not_import_validation() -> None:
    for path in GEOMETRY_ROOT.rglob("*.py"):
        assert not any(item.startswith("nollm.dream_geometry.validation") for item in _imports(path))


def test_dg1_bd_04_no_legacy_tree_or_anchor_public_fields() -> None:
    public_names = set()
    for path in GEOMETRY_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and not node.name.startswith("_"):
                public_names.add(node.name)
            elif isinstance(node, ast.arg):
                public_names.add(node.arg)
    lowered = {name.lower() for name in public_names}
    assert not (lowered & FORBIDDEN_PUBLIC_FIELDS)


def test_dg1_bd_05_no_third_party_dependency_files_added() -> None:
    forbidden = ["requirements.txt", "pyproject.toml", "package.json", "node_modules"]
    assert not any((REPO_ROOT / name).exists() for name in forbidden if name != "pyproject.toml")


def _imports(path: pathlib.Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = "." * node.level + (node.module or "")
            imports.add(module)
    return imports
