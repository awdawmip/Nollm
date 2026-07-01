import ast
import pathlib
from dataclasses import dataclass

from nollm.dream_geometry.protocol.contracts import ModuleName
from nollm.dream_geometry.protocol.dependency_rules import ALLOWED_DEPENDENCIES, is_dependency_allowed


REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
V2_ROOT = REPO_ROOT / "reference" / "python" / "nollm" / "dream_geometry"
V1_ROOT = REPO_ROOT / "reference" / "python" / "nollm"
V2_ROOT_MODULE = "nollm.dream_geometry"
V2_MODULE_NAMES = frozenset(item.value for item in ModuleName)
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
    "runpy",
    "pkgutil",
    "ctypes",
)
FORBIDDEN_DYNAMIC_MODULES = {"importlib", "runpy", "pkgutil", "ctypes"}
FORBIDDEN_DYNAMIC_CALLS = {"__import__", "exec", "compile"}
FORBIDDEN_RUNTIME_NAMES = {
    "agent_trial",
    "register_command",
    "add_subparsers",
    "write_card",
    "update_status",
}


@dataclass(frozen=True)
class ImportEdge:
    importer_path: pathlib.Path
    importer_module: str
    imported_module: str
    lineno: int
    form: str


@dataclass(frozen=True)
class FirewallViolation:
    path: pathlib.Path
    lineno: int
    reason: str


def module_name_for_path(path: pathlib.Path, root: pathlib.Path = V2_ROOT, root_module: str = V2_ROOT_MODULE) -> str:
    relative = path.relative_to(root).with_suffix("")
    parts = list(relative.parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join([root_module, *parts]) if parts else root_module


def top_v2_module(module_name: str) -> ModuleName | None:
    if module_name == V2_ROOT_MODULE:
        return ModuleName.protocol
    if not module_name.startswith(f"{V2_ROOT_MODULE}."):
        return None
    part = module_name.split(".")[2]
    if part in V2_MODULE_NAMES:
        return ModuleName(part)
    return None


def resolve_relative_import(importer_module: str, level: int, module: str | None) -> str:
    package = importer_module if (V2_ROOT / pathlib.Path(*importer_module.split(".")[2:]) / "__init__.py").exists() else importer_module.rpartition(".")[0]
    package_parts = package.split(".")
    if level > len(package_parts):
        return "." * level + (module or "")
    base = package_parts[: len(package_parts) - level + 1]
    if module:
        base.extend(module.split("."))
    return ".".join(base)


def extract_import_edges(source: str, path: pathlib.Path, root: pathlib.Path = V2_ROOT, root_module: str = V2_ROOT_MODULE) -> list[ImportEdge]:
    importer_module = module_name_for_path(path, root, root_module)
    tree = ast.parse(source)
    edges: list[ImportEdge] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                edges.append(ImportEdge(path, importer_module, alias.name, node.lineno, "import"))
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = resolve_relative_import(importer_module, node.level, node.module)
                form = "relative_from"
            else:
                base = node.module or ""
                form = "from"
            if node.names and node.names[0].name == "*":
                edges.append(ImportEdge(path, importer_module, base, node.lineno, form))
            else:
                for alias in node.names:
                    imported = f"{base}.{alias.name}" if base else alias.name
                    edges.append(ImportEdge(path, importer_module, imported, node.lineno, form))
        elif isinstance(node, ast.Call):
            dynamic_name = dynamic_import_target(node)
            if dynamic_name is not None:
                edges.append(ImportEdge(path, importer_module, dynamic_name, node.lineno, "dynamic_import"))
    return edges


def dynamic_import_target(node: ast.Call) -> str | None:
    func = node.func
    is_import_module = isinstance(func, ast.Attribute) and func.attr == "import_module" and isinstance(func.value, ast.Name) and func.value.id == "importlib"
    is_direct_import_module = isinstance(func, ast.Name) and func.id == "import_module"
    if not (is_import_module or is_direct_import_module):
        return None
    if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
        return node.args[0].value
    return "<dynamic-import>"


def extract_firewall_violations(source: str, path: pathlib.Path, root: pathlib.Path = V2_ROOT) -> list[FirewallViolation]:
    violations: list[FirewallViolation] = []
    for edge in extract_import_edges(source, path, root):
        if edge.imported_module in FORBIDDEN_DYNAMIC_MODULES or edge.imported_module.startswith(tuple(f"{item}." for item in FORBIDDEN_DYNAMIC_MODULES)):
            violations.append(FirewallViolation(path, edge.lineno, f"dynamic import module {edge.imported_module}"))
        if edge.imported_module.startswith(FORBIDDEN_MODULE_PREFIXES):
            violations.append(FirewallViolation(path, edge.lineno, f"forbidden module {edge.imported_module}"))
        if edge.imported_module.startswith("nollm.") and not edge.imported_module.startswith(V2_ROOT_MODULE):
            violations.append(FirewallViolation(path, edge.lineno, f"forbidden V1/runtime import {edge.imported_module}"))
        importer = top_v2_module(edge.importer_module)
        imported = top_v2_module(edge.imported_module)
        if importer is not None and imported is not None and not is_dependency_allowed(importer, imported):
            violations.append(FirewallViolation(path, edge.lineno, f"forbidden V2 edge {importer.value}->{imported.value}"))

    tree = ast.parse(source)
    import_module_aliases: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "importlib":
            for alias in node.names:
                if alias.name == "import_module":
                    import_module_aliases.add(alias.asname or alias.name)
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in FORBIDDEN_DYNAMIC_CALLS:
                violations.append(FirewallViolation(path, node.lineno, f"forbidden dynamic call {func.id}"))
            elif isinstance(func, ast.Name) and func.id in import_module_aliases:
                violations.append(FirewallViolation(path, node.lineno, "forbidden import_module alias call"))
        elif isinstance(node, (ast.Name, ast.Attribute)):
            name = node.id if isinstance(node, ast.Name) else node.attr
            if name.lower() in FORBIDDEN_RUNTIME_NAMES:
                violations.append(FirewallViolation(path, getattr(node, "lineno", 0), f"forbidden runtime name {name}"))
    return violations


def assert_source_clean(source: str, relative_path: str) -> None:
    path = V2_ROOT / relative_path
    violations = extract_firewall_violations(source, path)
    assert not violations, violations


def assert_source_rejected(source: str, relative_path: str, expected_reason: str) -> None:
    path = V2_ROOT / relative_path
    violations = extract_firewall_violations(source, path)
    assert any(expected_reason in violation.reason for violation in violations), violations


def test_import_edge_extractor_expands_from_and_relative_forms() -> None:
    path = V2_ROOT / "geometry" / "_sample.py"
    source = "\n".join(
        [
            "import nollm.openclaw_active_memory_adapter",
            "from nollm import openclaw_active_memory_adapter",
            "from nollm.dream_geometry import adapters",
            "from nollm.dream_geometry.adapters import receipt",
            "from .. import adapters",
            "from ..adapters import receipt",
            "from . import contracts",
            "from .contracts import ModuleName",
        ]
    )
    imported = [edge.imported_module for edge in extract_import_edges(source, path)]
    assert "nollm.openclaw_active_memory_adapter" in imported
    assert "nollm.openclaw_active_memory_adapter" in imported
    assert "nollm.dream_geometry.adapters" in imported
    assert "nollm.dream_geometry.adapters.receipt" in imported
    assert "nollm.dream_geometry.geometry.contracts" in imported
    assert "nollm.dream_geometry.geometry.contracts.ModuleName" in imported


def test_v2_ast_import_graph_satisfies_dependency_dag() -> None:
    violations: list[FirewallViolation] = []
    for path in V2_ROOT.rglob("*.py"):
        violations.extend(extract_firewall_violations(path.read_text(encoding="utf-8"), path))
    assert not violations, violations


def test_existing_v1_modules_do_not_import_v2_namespace() -> None:
    for path in V1_ROOT.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        edges = extract_import_edges(source, path, V1_ROOT, "nollm")
        assert not any(edge.imported_module == V2_ROOT_MODULE or edge.imported_module.startswith(f"{V2_ROOT_MODULE}.") for edge in edges)


def test_firewall_rejects_relative_import_bypass() -> None:
    assert_source_rejected("from .. import adapters\n", "geometry/_audit_relative_import_bypass.py", "geometry->adapters")


def test_firewall_rejects_root_package_openclaw_bypass() -> None:
    assert_source_rejected("from nollm import openclaw_active_memory_adapter\n", "geometry/_audit_root_import_bypass.py", "V1/runtime")


def test_firewall_rejects_importlib_import_module() -> None:
    assert_source_rejected('import importlib\nimportlib.import_module("nollm.openclaw_active_memory_adapter")\n', "geometry/_audit_dynamic.py", "dynamic import")


def test_firewall_rejects_import_module_alias() -> None:
    assert_source_rejected('from importlib import import_module as im\nim("nollm.openclaw_active_memory_adapter")\n', "geometry/_audit_dynamic_alias.py", "dynamic import")


def test_firewall_rejects_dunder_import() -> None:
    assert_source_rejected('__import__("nollm.openclaw_active_memory_adapter")\n', "geometry/_audit_dunder.py", "dynamic call __import__")


def test_documented_dependency_matrix_matches_executable_rules() -> None:
    expected = {
        "evidence -> protocol",
        "geometry -> protocol",
        "cortex -> protocol, evidence",
        "field -> protocol, evidence, geometry",
        "admission -> protocol, evidence, geometry, field, cortex",
        "recall -> protocol, evidence, geometry, field, cortex",
        "adapters -> protocol, evidence, cortex, recall",
        "validation -> protocol, evidence, geometry, field, cortex, admission, recall, adapters",
    }
    docs = "\n".join(
        [
            (REPO_ROOT / "protocol" / "v2" / "MODULE_DEPENDENCY_RULES.md").read_text(encoding="utf-8"),
            (REPO_ROOT / "docs" / "architecture" / "NOLLM_V2_MODULE_BOUNDARIES_DG0.md").read_text(encoding="utf-8"),
        ]
    )
    for line in expected:
        assert line in docs
    rendered = {
        f"{importer.value} -> {', '.join(imported.value for imported in ModuleName if (importer, imported) in ALLOWED_DEPENDENCIES)}"
        for importer in ModuleName
        if any(edge[0] == importer for edge in ALLOWED_DEPENDENCIES)
    }
    assert rendered == expected
