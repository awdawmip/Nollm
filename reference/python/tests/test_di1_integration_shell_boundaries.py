from __future__ import annotations

import ast
from pathlib import Path

from nollm.dream_geometry.adapters import RecallInvocation
from nollm.dream_geometry.validation.di1_integration_fixture import build_di1_context
from subprocess_harness import run_subprocess


ROOT = Path(__file__).resolve().parents[3]
ADAPTERS = ROOT / "reference" / "python" / "nollm" / "dream_geometry" / "adapters"
FORBIDDEN_IMPORT_FRAGMENTS = (
    "dream_geometry.geometry",
    "dream_geometry.field",
    "recall.traversal",
    "recall.projection",
    "recall.qualification",
    "recall.universe",
    "cortex.compiler",
    "openclaw",
    "runtime",
    "memory",
    "sqlite",
    "socket",
    "requests",
    "urllib",
    "subprocess",
)
FORBIDDEN_CALL_NAMES = ("put_", "record_", "compile_", "open_store")


def test_t_707_raw_text_or_query_draft_cannot_enter_recall(tmp_path) -> None:
    _, _, _, invocation, context = build_di1_context(tmp_path)
    bad = object.__new__(RecallInvocation)
    object.__setattr__(bad, "request_id", invocation.request_id)
    object.__setattr__(bad, "operation", "recall")
    object.__setattr__(bad, "query_probe", {"query_text": "Kunming rain yesterday?"})
    mapping = __import__("nollm.dream_geometry.adapters", fromlist=["IntegrationShell"]).IntegrationShell().handle(bad, context).to_mapping()
    assert mapping["error"]["code"] == "DI1_INVALID_INVOCATION"


def test_t_708_709_invocation_slots_prevent_policy_path_or_selector_fields(tmp_path) -> None:
    _, _, _, invocation, _ = build_di1_context(tmp_path)
    for name in ("recall_policy", "store_path", "universe_selector", "chart", "cell", "seed", "gravity"):
        try:
            object.__setattr__(invocation, name, "forbidden")
        except (AttributeError, TypeError):
            pass
        assert not hasattr(invocation, name)


def test_t_728_adapters_do_not_import_forbidden_modules() -> None:
    offenders = []
    for path in sorted(ADAPTERS.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                modules = [node.module or ""]
            else:
                continue
            for module in modules:
                lowered = module.lower()
                if any(fragment in lowered for fragment in FORBIDDEN_IMPORT_FRAGMENTS):
                    offenders.append(f"{path.name}:{module}")
    assert offenders == []


def test_t_729_adapters_do_not_call_writes_compilers_or_private_attrs() -> None:
    offenders = []
    for path in sorted(ADAPTERS.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr.startswith("_") and not (node.attr.startswith("__") and node.attr.endswith("__")):
                offenders.append(f"{path.name}:{node.attr}")
            elif isinstance(node, ast.Call):
                func = node.func
                name = func.attr if isinstance(func, ast.Attribute) else func.id if isinstance(func, ast.Name) else ""
                if name.startswith(FORBIDDEN_CALL_NAMES):
                    offenders.append(f"{path.name}:{name}")
    assert offenders == []


def test_t_730_sealed_paths_are_not_modified_in_worktree() -> None:
    result = run_subprocess(
        ["git", "diff", "--name-only", "--", "reference/python/nollm/dream_geometry/geometry", "reference/python/nollm/dream_geometry/field", "reference/python/nollm/dream_geometry/evidence", "reference/python/nollm/dream_geometry/cortex", "reference/python/nollm/dream_geometry/recall"],
        cwd=ROOT,
        timeout_seconds=10,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == ""
