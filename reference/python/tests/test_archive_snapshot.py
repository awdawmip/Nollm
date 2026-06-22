from __future__ import annotations

import json
from pathlib import Path

import pytest

from nollm.archive import create_archive_snapshot, verify_archive_snapshot
from nollm.archive_manifest import sha256_bytes


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "mt1" / "legacy_workspace"


def test_archive_snapshot_preserves_source_bytes(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    copy_fixture(FIXTURE, workspace)
    before = file_hashes(workspace)
    report = create_archive_snapshot(workspace, tmp_path / "memory-root")
    after = file_hashes(workspace)

    assert report["ok"] is True
    assert before == after
    verify = verify_archive_snapshot(tmp_path / "memory-root", str(report["snapshot_id"]))
    assert verify["ok"] is True


def test_archive_verify_fails_on_tamper(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    copy_fixture(FIXTURE, workspace)
    report = create_archive_snapshot(workspace, tmp_path / "memory-root")
    manifest = tmp_path / "memory-root" / "archive" / "manifests" / f"{report['snapshot_id']}.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    digest = data["sources"][0]["content_hash"].removeprefix("sha256:")
    (tmp_path / "memory-root" / "archive" / "objects" / "sha256" / digest).write_text("tampered", encoding="utf-8")

    verify = verify_archive_snapshot(tmp_path / "memory-root", str(report["snapshot_id"]))

    assert verify["ok"] is False
    assert any("hash_mismatch" in error for error in verify["errors"])


def test_archive_rejects_symlink_escape(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    copy_fixture(FIXTURE, workspace)
    outside = tmp_path / "outside.md"
    outside.write_text("secret", encoding="utf-8")
    link = workspace / "memory" / "escape.md"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("symlink creation unavailable")

    result = create_archive_snapshot(workspace, tmp_path / "memory-root")

    assert result["ok"] is False
    assert any("symlink" in error for error in result["errors"])


def file_hashes(root: Path) -> dict[str, str]:
    return {path.relative_to(root).as_posix(): sha256_bytes(path.read_bytes()) for path in sorted(root.rglob("*.md"))}


def copy_fixture(src: Path, dst: Path) -> None:
    for path in src.rglob("*"):
        if path.is_file():
            target = dst / path.relative_to(src)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())
