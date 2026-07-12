"""Validate ownership truthfulness and migration invariants."""

from __future__ import annotations

import json
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
