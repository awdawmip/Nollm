"""Executable GRF4R Core and geometry readiness checks."""

from __future__ import annotations

import ast
from pathlib import Path

from .kernel_registry import KernelRegistry
from .profiles import get_profile, profiles


def core_readiness() -> dict[str, bool]:
    root = Path(__file__).resolve().parent
    forbidden_import_roots = {"integrations", "openclaw", "codex", "terminal"}
    core_independent = True
    for path in root.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = {alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
        imports |= {node.module.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
        core_independent = core_independent and not bool(imports & forbidden_import_roots)
    registry = KernelRegistry()
    registry.compile_profiles(tuple(profile.profile_id for profile in profiles()))
    small = registry.compression_report(100_000)
    large = registry.compression_report(1_000_000)
    exact = get_profile("eisenstein_exact_v1")
    return {
        "core_independent": core_independent,
        "runtime_no_polygon": all(not profile.runtime_polygon for profile in profiles()),
        "exact_runtime_no_float": not exact.runtime_float_allowed,
        "kernel_reusable": small.compressed_size == large.compressed_size and small.raw_entries == large.raw_entries,
        "kernel_reconstruction_exact": small.reconstruction_error == 0 and large.reconstruction_error == 0,
    }
