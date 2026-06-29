import ast
import pathlib

from nollm.dream_geometry.protocol.contracts import ModuleName
from nollm.dream_geometry.protocol.dependency_rules import is_dependency_allowed


REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
V2_ROOT = REPO_ROOT / "reference" / "python" / "nollm" / "dream_geometry"
V1_ROOT = REPO_ROOT / "reference" / "python" / "nollm"
FORBIDDEN_MODULE_PREFIXES = (
    "nollm.openclaw_",
    "nollm.native_field",
    "nollm.cli",
    "nollm.recall",
    "subprocess",
    "socket",
    "requests",
    "http",
    "urllib",
)
FORBIDDEN_RUNTIME_STRINGS = (
    "agent_trial",
    "plugin install",
    "register_command",
    "add_subparsers",
    "write_card",
    "update_status",
    "native memory",
)


def parse_imports(source: str) -> set[str]:
    tree = ast.parse(source)
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = "." * node.level + (node.module or "")
            imports.add(module)
    return imports


def runtime_code_tokens(source: str) -> set[str]:
    tree = ast.parse(source)
    tokens: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            tokens.add(node.id.lower())
        elif isinstance(node, ast.Attribute):
            tokens.add(node.attr.lower())
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                tokens.add(func.id.lower())
            elif isinstance(func, ast.Attribute):
                tokens.add(func.attr.lower())
    return tokens


def v2_module_for_path(path: pathlib.Path) -> ModuleName:
    relative = path.relative_to(V2_ROOT)
    part = relative.parts[0]
    if part == "__init__.py":
        return ModuleName.protocol
    return ModuleName(part)


def resolve_v2_import(importer: ModuleName, import_name: str) -> ModuleName | None:
    if import_name.startswith("nollm.dream_geometry."):
        part = import_name.split(".")[2]
        return ModuleName(part)
    if import_name == "nollm.dream_geometry":
        return ModuleName.protocol
    if import_name.startswith("."):
        stripped = import_name.lstrip(".")
        if not stripped:
            return importer
        part = stripped.split(".")[0]
        if part in {item.value for item in ModuleName}:
            return ModuleName(part)
        return importer
    return None


def test_v2_ast_import_graph_satisfies_dependency_dag() -> None:
    for path in V2_ROOT.rglob("*.py"):
        importer = v2_module_for_path(path)
        imports = parse_imports(path.read_text(encoding="utf-8"))
        for import_name in imports:
            imported = resolve_v2_import(importer, import_name)
            if imported is not None:
                assert is_dependency_allowed(importer, imported), f"{path} imports {import_name}"


def test_v2_forbids_runtime_openclaw_network_and_subprocess_imports() -> None:
    for path in V2_ROOT.rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        imports = parse_imports(source)
        for import_name in imports:
            assert not import_name.startswith(FORBIDDEN_MODULE_PREFIXES), f"{path} imports {import_name}"
        tokens = runtime_code_tokens(source)
        for token in FORBIDDEN_RUNTIME_STRINGS:
            assert token not in tokens, f"{path} contains forbidden runtime token {token}"


def test_existing_v1_modules_do_not_import_v2_namespace() -> None:
    for path in V1_ROOT.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        imports = parse_imports(source)
        assert "nollm.dream_geometry" not in imports
        assert not any(item.startswith("nollm.dream_geometry.") for item in imports)


def test_firewall_detector_catches_intentional_forbidden_import() -> None:
    imports = parse_imports("from nollm.dream_geometry.adapters import receipt\n")
    imported = resolve_v2_import(ModuleName.geometry, next(iter(imports)))
    assert imported is ModuleName.adapters
    assert not is_dependency_allowed(ModuleName.geometry, imported)
