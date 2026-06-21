from __future__ import annotations

from pathlib import Path

from nollm.archive import create_archive_snapshot
from nollm.legacy_import import legacy_import_report, plan_legacy_import, run_legacy_import, validate_legacy_import


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "mt1" / "legacy_workspace"


def test_plan_dry_run_commit_validate_and_idempotence(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    copy_fixture(FIXTURE, workspace)
    memory_root = tmp_path / "memory-root"
    snapshot_id = str(create_archive_snapshot(workspace, memory_root)["snapshot_id"])
    source_hashes_before = file_hashes(workspace)

    plan = plan_legacy_import(memory_root, snapshot_id, target_field_id="field_fixture")
    dry_run = run_legacy_import(memory_root, str(plan["batch_id"]), dry_run=True)
    commit = run_legacy_import(memory_root, str(plan["batch_id"]), commit=True)
    source_hashes_after = file_hashes(workspace)
    validate = validate_legacy_import(memory_root, str(plan["batch_id"]))
    duplicate = run_legacy_import(memory_root, str(plan["batch_id"]), commit=True)
    receipt = (memory_root / "ingress" / "legacy-import" / str(plan["batch_id"]) / "import-receipt.json").read_text(encoding="utf-8")

    assert plan["ok"] is True
    assert dry_run["ok"] is True
    assert dry_run["candidate_shard_count"] == 3
    assert commit["created_shard_count"] == 3
    assert duplicate["created_shard_count"] == 0
    assert duplicate["duplicate_count"] == 3
    assert validate["ok"] is True
    assert source_hashes_before == source_hashes_after
    assert '"created_shard_count": 3' in receipt


def test_validate_and_report_do_not_need_source_workspace_after_snapshot(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    copy_fixture(FIXTURE, workspace)
    memory_root = tmp_path / "memory-root"
    snapshot_id = str(create_archive_snapshot(workspace, memory_root)["snapshot_id"])
    plan = plan_legacy_import(memory_root, snapshot_id, target_field_id="field_fixture")
    commit = run_legacy_import(memory_root, str(plan["batch_id"]), commit=True)
    workspace.rename(tmp_path / "workspace.moved")

    validate = validate_legacy_import(memory_root, str(plan["batch_id"]))
    report = legacy_import_report(memory_root, str(plan["batch_id"]))
    duplicate = run_legacy_import(memory_root, str(plan["batch_id"]), commit=True)

    assert commit["ok"] is True
    assert validate["ok"] is True
    assert report["validation"]["ok"] is True
    assert duplicate["created_shard_count"] == 0


def copy_fixture(src: Path, dst: Path) -> None:
    for path in src.rglob("*"):
        if path.is_file():
            target = dst / path.relative_to(src)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())


def file_hashes(root: Path) -> dict[str, str]:
    import hashlib

    return {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(root.rglob("*.md"))}
