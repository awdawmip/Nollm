import ast
import importlib
import pathlib
import sys


REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
EVIDENCE_ROOT = REPO_ROOT / "reference" / "python" / "nollm" / "dream_geometry" / "evidence"
ALLOWED_ROOTS = {
    "__future__",
    "dataclasses",
    "datetime",
    "hashlib",
    "json",
    "pathlib",
    "typing",
    "nollm",
}
FORBIDDEN_V2 = {
    "nollm.dream_geometry.geometry",
    "nollm.dream_geometry.field",
    "nollm.dream_geometry.cortex",
    "nollm.dream_geometry.recall",
    "nollm.dream_geometry.adapters",
    "nollm.dream_geometry.validation",
}
FORBIDDEN_ROOTS = {"subprocess", "socket", "requests", "http", "urllib", "sqlite3", "random", "uuid", "time"}


def _imports(path: pathlib.Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules.append("." * node.level + (node.module or ""))
    return modules


def test_de1_t340_evidence_imports_only_protocol_and_stdlib() -> None:
    for path in EVIDENCE_ROOT.glob("*.py"):
        for module in _imports(path):
            if module.startswith("."):
                continue
            root = module.lstrip(".").split(".", 1)[0]
            assert root in ALLOWED_ROOTS, (path, module)
            assert root not in FORBIDDEN_ROOTS, (path, module)
            assert not any(module.startswith(prefix) for prefix in FORBIDDEN_V2), (path, module)


def test_de1_t341_fresh_import_has_no_runtime_or_field_imports(tmp_path, monkeypatch) -> None:
    before = set(tmp_path.iterdir())
    modules_before = set(sys.modules)
    module = importlib.import_module("nollm.dream_geometry.evidence")
    assert module.__all__
    after = set(tmp_path.iterdir())
    assert after == before
    modules_after = set(sys.modules)
    newly_imported = modules_after - modules_before
    assert "nollm.dream_geometry.field" not in newly_imported
    assert "nollm.dream_geometry.geometry" not in newly_imported


def test_de1_report_uses_synthetic_fixtures() -> None:
    from nollm.dream_geometry.validation.de1_memory_substrate_report import build_report

    report = build_report()
    assert "DE1 Memory Substrate Baseline Report" in report
    assert "synthetic_only" in report
    assert "F-A same text distinct occurrences | pass" in report
    assert "F-J opaque field-style refs preserved | pass" in report
    assert "OpenClaw/runtime/CLI/adapters" in report
