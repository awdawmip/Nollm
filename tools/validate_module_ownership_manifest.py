"""Validate ownership truthfulness and migration invariants."""

from __future__ import annotations

import json
import ast
import subprocess
import sys
from pathlib import Path
from typing import Iterable

from generate_module_ownership_manifest import ROOT, module_name, tracked_files


MANIFEST = ROOT / "docs" / "architecture" / "module-ownership" / "MODULE_OWNERSHIP_MANIFEST.json"
UNCLASSIFIED = ROOT / "docs" / "architecture" / "module-ownership" / "UNCLASSIFIED_TRACKED_FILES.txt"
CONFIG = ROOT / "config" / "module-boundaries.json"

OWNERS = {"CORE", "SNAPSHOT", "TRACE", "ACCESS", "HISTORY", "AUDIT", "OPENCLAW", "LAB", "DISTRIBUTION", "LEGACY", "DELETE"}
LIFECYCLES = {"ACTIVE", "CANDIDATE", "MIGRATION_ASSET", "BLOCKED", "HISTORICAL", "GENERATED"}
ACTIONS = {"KEEP", "MOVE", "SPLIT", "WRAP_TEMPORARILY", "QUARANTINE", "DELETE_LATER", "DELETE_NOW"}
CONFIDENCES = {"HIGH", "MEDIUM", "LOW"}
MIGRATION_STATUSES = {"NOT_APPLICABLE", "PENDING", "COMPLETED", "BLOCKED_BY_SPLIT", "QUARANTINED"}
REVIEW_STATUSES = {"AUTO_CANDIDATE", "CODE_REVIEWED", "DEPENDENCY_REVIEWED", "MOVE_VERIFIED"}
DELETE_ACTIONS = {"DELETE_LATER", "DELETE_NOW"}
PUBLIC_PACKAGE_FILES = {
    "nollm_core": "packages/nollm-core/src/nollm_core/__init__.py",
    "nollm_access": "packages/nollm-access/src/nollm_access/__init__.py",
    "nollm_snapshot": "packages/nollm-snapshot/src/nollm_snapshot/__init__.py",
    "nollm_trace": "packages/nollm-trace/src/nollm_trace/__init__.py",
}
LAB_ASSET_CLASSES = {
    "ACTIVE_LIBRARY", "ACTIVE_TOOL", "ACTIVE_FIXTURE", "ACTIVE_TEST",
    "ACTIVE_VALIDATION", "ACTIVE_REPOSITORY_TOOL", "LEGACY_REGRESSION",
    "LEGACY_REFERENCE", "HISTORICAL_RESULT",
}
CONTRACT_ASSET_CLASSES = {
    "ACTIVE_LIBRARY", "ACTIVE_TOOL", "ACTIVE_VALIDATION", "ACTIVE_REPOSITORY_TOOL",
}
GATED_ASSET_CLASSES = {
    "ACTIVE_LIBRARY", "ACTIVE_TOOL", "ACTIVE_FIXTURE", "ACTIVE_TEST",
    "ACTIVE_VALIDATION", "ACTIVE_REPOSITORY_TOOL", "LEGACY_REGRESSION",
}
VALIDATION_GATES = {
    "package:core", "package:snapshot", "package:trace", "package:access",
    "governance:m0", "governance:architecture", "compatibility:grf",
    "lab:compiled-templates", "lab:geometry-parity", "lab:core-capability",
    "lab:minimal-e2e", "repository:manifest", "repository:boundary",
}
GATE_TARGETS = {
    "package:core": "packages/nollm-core/tests",
    "package:snapshot": "packages/nollm-snapshot/tests",
    "package:trace": "packages/nollm-trace/tests",
    "package:access": "packages/nollm-access/tests",
    "governance:m0": "reference/python/tests/m0",
    "governance:architecture": "reference/python/tests/test_architecture_language.py",
    "compatibility:grf": "reference/python/tests/grf",
    "lab:compiled-templates": "lab/nollm-lab/geometry/generate_compiled_templates.py",
    "lab:geometry-parity": "lab/nollm-lab/m1/run_geometry_parity.py",
    "lab:core-capability": "lab/nollm-lab/m1/run_core_capability_validation.py",
    "lab:minimal-e2e": "lab/nollm-lab/m1/run_m1_minimal_e2e.py",
    "repository:manifest": "tools/generate_module_ownership_manifest.py",
    "repository:boundary": "tools/check_module_boundaries.py",
}


def package_exports(root: Path, package: str) -> set[str]:
    tree = ast.parse((root / PUBLIC_PACKAGE_FILES[package]).read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets):
            return set(ast.literal_eval(node.value))
    raise ValueError(f"{package} has no literal __all__")


def active_lab_contract_errors(row: dict[str, object], root: Path) -> list[str]:
    path = str(row.get("path", ""))
    if not (row.get("owner") == "LAB" and row.get("asset_class") in CONTRACT_ASSET_CLASSES and row.get("file_type") == "py"):
        return []
    tree = ast.parse((root / path).read_text(encoding="utf-8"), filename=path)
    errors = []
    exports = {package: package_exports(root, package) for package in PUBLIC_PACKAGE_FILES}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if any(alias.name.startswith(package + ".") for package in PUBLIC_PACKAGE_FILES):
                    errors.append(f"{path}: ACTIVE Lab imports private package submodule {alias.name}")
        elif isinstance(node, ast.ImportFrom) and node.module:
            if any(node.module.startswith(package + ".") for package in PUBLIC_PACKAGE_FILES):
                errors.append(f"{path}: ACTIVE Lab imports private package submodule {node.module}")
            elif node.module in exports:
                for alias in node.names:
                    if alias.name not in exports[node.module]:
                        errors.append(f"{path}: ACTIVE Lab imports missing public symbol {node.module}.{alias.name}")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in {"__import__", "import_module"}:
                errors.append(f"{path}: ACTIVE Lab uses dynamic {node.func.id}")
            elif (
                isinstance(node.func, ast.Name)
                and node.func.id == "getattr"
                and node.args
                and isinstance(node.args[0], ast.Name)
                and node.args[0].id in PUBLIC_PACKAGE_FILES
            ):
                errors.append(f"{path}: ACTIVE Lab uses dynamic getattr on {node.args[0].id}")
            elif isinstance(node.func, ast.Attribute) and node.func.attr == "import_module":
                errors.append(f"{path}: ACTIVE Lab uses dynamic import_module")
    return errors


def resolve_import(imported: str, modules: dict[str, str]) -> str | None:
    parts = imported.split(".")
    for length in range(len(parts), 0, -1):
        target = modules.get(".".join(parts[:length]))
        if target:
            return target
    return None


def validate_rows(
    rows: list[dict[str, object]],
    tracked: Iterable[str],
    root: Path,
    config: dict[str, object],
) -> list[str]:
    errors: list[str] = []
    paths = [str(row.get("path", "")) for row in rows]
    path_set = set(paths)
    tracked_set = set(tracked)
    if len(paths) != len(path_set):
        errors.append("manifest contains duplicate paths")
    missing = sorted(tracked_set - path_set)
    stale = sorted(path_set - tracked_set)
    if missing:
        errors.append("tracked files missing from manifest: " + ", ".join(missing))
    if stale:
        errors.append("stale manifest paths: " + ", ".join(stale))

    by_path = {str(row["path"]): row for row in rows if row.get("path")}
    modules = {name: path for path in path_set if (name := module_name(path))}
    allowed = {
        owner: set(settings["allowed"])
        for owner, settings in config["modules"].items()
    }
    allowed["LAB"] |= {"LEGACY", "DISTRIBUTION"}

    for row in rows:
        path = str(row.get("path", "<missing>"))
        owner = str(row.get("owner", ""))
        lifecycle = str(row.get("lifecycle_status", ""))
        action = str(row.get("migration_action", ""))
        confidence = str(row.get("confidence", ""))
        migration_status = str(row.get("migration_status", ""))
        review_status = str(row.get("review_status", ""))
        asset_class = str(row.get("asset_class", ""))
        validation_gate = str(row.get("validation_gate", ""))
        if owner not in OWNERS:
            errors.append(f"{path}: invalid owner {owner}")
        if lifecycle not in LIFECYCLES:
            errors.append(f"{path}: invalid lifecycle_status {lifecycle}")
        if action not in ACTIONS:
            errors.append(f"{path}: invalid migration_action {action}")
        if confidence not in CONFIDENCES:
            errors.append(f"{path}: invalid confidence {confidence}")
        if migration_status not in MIGRATION_STATUSES:
            errors.append(f"{path}: invalid migration_status {migration_status}")
        if review_status not in REVIEW_STATUSES:
            errors.append(f"{path}: invalid review_status {review_status}")
        if owner == "LAB":
            if asset_class not in LAB_ASSET_CLASSES:
                errors.append(f"{path}: invalid or missing LAB asset_class {asset_class}")
            if asset_class.startswith("ACTIVE_") and lifecycle != "ACTIVE":
                errors.append(f"{path}: {asset_class} requires ACTIVE lifecycle")
            if asset_class == "LEGACY_REGRESSION" and lifecycle != "MIGRATION_ASSET":
                errors.append(f"{path}: LEGACY_REGRESSION requires MIGRATION_ASSET lifecycle")
            if asset_class in {"LEGACY_REFERENCE", "HISTORICAL_RESULT"} and lifecycle != "HISTORICAL":
                errors.append(f"{path}: {asset_class} requires HISTORICAL lifecycle")
            if asset_class in GATED_ASSET_CLASSES and not validation_gate:
                errors.append(f"{path}: {asset_class} requires validation_gate")
            if validation_gate and validation_gate not in VALIDATION_GATES:
                errors.append(f"{path}: unknown validation_gate {validation_gate}")
            if validation_gate in GATE_TARGETS and not (root / GATE_TARGETS[validation_gate]).exists():
                errors.append(f"{path}: validation_gate target does not exist: {GATE_TARGETS[validation_gate]}")
            if asset_class in {"LEGACY_REFERENCE", "HISTORICAL_RESULT"} and validation_gate:
                errors.append(f"{path}: {asset_class} must not enter an active gate")
        elif asset_class or validation_gate:
            errors.append(f"{path}: non-LAB asset must not define asset_class or validation_gate")

        target = str(row.get("target_path", ""))
        if action == "MOVE":
            if not target:
                errors.append(f"{path}: MOVE requires target_path")
            if migration_status not in {"PENDING", "COMPLETED"}:
                errors.append(f"{path}: MOVE requires PENDING or COMPLETED migration_status")
            if confidence == "HIGH" and migration_status == "PENDING":
                errors.append(f"{path}: HIGH + MOVE + PENDING is forbidden")
        if action == "MOVE" and migration_status == "COMPLETED":
            if not target or not (root / target).exists():
                errors.append(f"{path}: completed MOVE target does not exist")
            source_exists = (root / path).exists()
            compat = "compat/" in path or "compatibility" in str(row.get("classification_evidence", "")).lower()
            if source_exists and path != target and not compat:
                errors.append(f"{path}: completed MOVE left an unregistered source implementation")

        forbidden = row.get("forbidden_feature_evidence", [])
        if action in DELETE_ACTIONS or lifecycle == "BLOCKED":
            if not isinstance(forbidden, list) or not forbidden:
                errors.append(f"{path}: BLOCKED/DELETE requires forbidden_feature_evidence")
            else:
                required = {"symbol", "file", "location", "correctness_dependency", "replacement_target"}
                for item in forbidden:
                    if not isinstance(item, dict) or not required <= set(item):
                        errors.append(f"{path}: forbidden feature evidence is incomplete")
                        break
        if confidence == "LOW" and action in DELETE_ACTIONS:
            errors.append(f"{path}: LOW confidence asset may not be deleted")

        evidence = str(row.get("classification_evidence", ""))
        if evidence.startswith("Unmatched path") and (
            owner != "LEGACY"
            or confidence != "LOW"
            or action != "QUARANTINE"
            or lifecycle != "MIGRATION_ASSET"
        ):
            errors.append(f"{path}: catch-all classification must be LEGACY + LOW + QUARANTINE")

        if confidence == "HIGH" and owner in allowed:
            for imported in row.get("imports", []):
                if not isinstance(imported, str):
                    continue
                target_path = resolve_import(imported, modules)
                if not target_path:
                    continue
                target_owner = str(by_path[target_path].get("owner", ""))
                if target_owner != owner and target_owner not in allowed[owner]:
                    errors.append(
                        f"{path}: HIGH file imports forbidden owner {target_owner} via {target_path}"
                    )
        errors.extend(active_lab_contract_errors(row, root))
    return sorted(set(errors))


def main() -> int:
    rows = json.loads(MANIFEST.read_text(encoding="utf-8"))
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    tracked = tracked_files()
    errors = validate_rows(rows, tracked, ROOT, config)
    expected_unclassified = sorted(set(tracked) - {str(row["path"]) for row in rows})
    actual_unclassified = UNCLASSIFIED.read_text(encoding="utf-8").splitlines()
    if actual_unclassified != expected_unclassified:
        errors.append("UNCLASSIFIED_TRACKED_FILES.txt does not equal the actual tracked difference")

    before = subprocess.run(
        ["git", "status", "--porcelain=v1"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout
    check = subprocess.run(
        [sys.executable, "tools/generate_module_ownership_manifest.py", "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    after = subprocess.run(
        ["git", "status", "--porcelain=v1"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout
    if check.returncode:
        errors.append("generator --check reports non-canonical manifest outputs")
    if before != after:
        errors.append("generator --check changed the working tree")
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"ownership manifest valid: tracked={len(tracked)} rows={len(rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
