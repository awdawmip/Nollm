from __future__ import annotations

import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools"))

from validate_module_ownership_manifest import validate_rows  # noqa: E402


CONFIG = {
    "modules": {
        "CORE": {"allowed": []},
        "SNAPSHOT": {"allowed": ["CORE"]},
        "TRACE": {"allowed": ["CORE"]},
        "ACCESS": {"allowed": ["CORE", "SNAPSHOT"]},
        "HISTORY": {"allowed": ["ACCESS", "SNAPSHOT"]},
        "AUDIT": {"allowed": ["ACCESS", "TRACE"]},
        "OPENCLAW": {"allowed": ["ACCESS"]},
        "LAB": {"allowed": ["CORE", "SNAPSHOT", "TRACE", "ACCESS", "HISTORY", "AUDIT", "OPENCLAW"]},
        "DISTRIBUTION": {"allowed": ["CORE", "SNAPSHOT", "TRACE", "ACCESS", "HISTORY", "AUDIT", "OPENCLAW"]},
    }
}


def row(path: str, **overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "path": path,
        "owner": "LEGACY",
        "lifecycle_status": "MIGRATION_ASSET",
        "migration_action": "QUARANTINE",
        "confidence": "LOW",
        "migration_status": "QUARANTINED",
        "review_status": "AUTO_CANDIDATE",
        "target_path": "",
        "imports": [],
        "classification_evidence": "Unmatched path; preserved conservatively.",
        "forbidden_feature_evidence": [],
    }
    value.update(overrides)
    return value


def errors(tmp_path: Path, rows: list[dict[str, object]], tracked: list[str] | None = None) -> list[str]:
    return validate_rows(rows, tracked or [str(item["path"]) for item in rows], tmp_path, CONFIG)


def test_rejects_high_file_with_forbidden_import(tmp_path: Path) -> None:
    source = row(
        "packages/nollm-core/src/nollm_core/source.py",
        owner="CORE",
        lifecycle_status="ACTIVE",
        migration_action="KEEP",
        confidence="HIGH",
        migration_status="NOT_APPLICABLE",
        review_status="DEPENDENCY_REVIEWED",
        imports=["nollm_access.target"],
        classification_evidence="Reviewed Core source.",
    )
    target = row(
        "packages/nollm-access/src/nollm_access/target.py",
        owner="ACCESS",
        lifecycle_status="ACTIVE",
        migration_action="KEEP",
        confidence="HIGH",
        migration_status="NOT_APPLICABLE",
        review_status="DEPENDENCY_REVIEWED",
        classification_evidence="Reviewed Access source.",
    )
    assert any("HIGH file imports forbidden owner ACCESS" in item for item in errors(tmp_path, [source, target]))


def test_rejects_move_without_target(tmp_path: Path) -> None:
    item = row("asset.py", migration_action="MOVE", confidence="MEDIUM", migration_status="PENDING")
    assert any("MOVE requires target_path" in value for value in errors(tmp_path, [item]))


def test_rejects_completed_move_with_missing_target(tmp_path: Path) -> None:
    item = row("asset.py", migration_action="MOVE", confidence="MEDIUM", migration_status="COMPLETED", target_path="missing.py")
    assert any("completed MOVE target does not exist" in value for value in errors(tmp_path, [item]))


def test_rejects_blocked_without_code_evidence(tmp_path: Path) -> None:
    item = row("blocked.py", lifecycle_status="BLOCKED", migration_action="SPLIT", confidence="MEDIUM", migration_status="BLOCKED_BY_SPLIT")
    assert any("BLOCKED/DELETE requires" in value for value in errors(tmp_path, [item]))


def test_rejects_low_confidence_delete(tmp_path: Path) -> None:
    item = row("delete.py", migration_action="DELETE_LATER")
    result = errors(tmp_path, [item])
    assert any("LOW confidence asset may not be deleted" in value for value in result)


def test_rejects_tracked_file_omission(tmp_path: Path) -> None:
    item = row("known.py")
    assert any("tracked files missing" in value for value in errors(tmp_path, [item], ["known.py", "missing.py"]))


def test_rejects_active_high_catch_all(tmp_path: Path) -> None:
    item = row("unknown.py", owner="CORE", lifecycle_status="ACTIVE", migration_action="KEEP", confidence="HIGH", migration_status="NOT_APPLICABLE")
    assert any("catch-all classification" in value for value in errors(tmp_path, [item]))
