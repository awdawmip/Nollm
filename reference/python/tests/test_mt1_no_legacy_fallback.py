from __future__ import annotations

import json
from pathlib import Path

from nollm.archive import create_archive_snapshot
from nollm.legacy_import import plan_legacy_import, run_legacy_import


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "mt1" / "legacy_workspace"


def test_plan_and_commit_do_not_fallback_to_legacy_source_after_snapshot(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    copy_fixture(FIXTURE, workspace)
    memory_root = tmp_path / "memory-root"
    snapshot_id = str(create_archive_snapshot(workspace, memory_root)["snapshot_id"])
    workspace.rename(tmp_path / "workspace.unavailable")

    plan = plan_legacy_import(memory_root, snapshot_id, target_field_id="field_fixture")
    commit = run_legacy_import(memory_root, str(plan["batch_id"]), commit=True)

    assert plan["ok"] is True
    assert commit["ok"] is True
    assert commit["created_shard_count"] == 3


def test_archive_tamper_blocks_commit_without_field_publish(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    copy_fixture(FIXTURE, workspace)
    memory_root = tmp_path / "memory-root"
    snapshot_id = str(create_archive_snapshot(workspace, memory_root)["snapshot_id"])
    plan = plan_legacy_import(memory_root, snapshot_id, target_field_id="field_fixture")
    manifest_path = next((memory_root / "archive" / "manifests").glob("*.json"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    digest = manifest["sources"][0]["content_hash"].removeprefix("sha256:")
    (memory_root / "archive" / "objects" / "sha256" / digest).write_text("tampered", encoding="utf-8")

    commit = run_legacy_import(memory_root, str(plan["batch_id"]), commit=True)

    assert commit["ok"] is False
    assert not (memory_root / "field" / "HEAD.json").exists()


def copy_fixture(src: Path, dst: Path) -> None:
    for path in src.rglob("*"):
        if path.is_file():
            target = dst / path.relative_to(src)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())
