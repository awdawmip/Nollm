from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import zipfile

from subprocess_harness import run_subprocess
from nollm.engineering_rc_archive import (
    build_engineering_rc_export_archive,
    verify_engineering_rc_export_archive,
)
from nollm.engineering_rc_export import HASH_MANIFEST_PATH, build_engineering_rc_artifact_hash_manifest, canonical_rc_artifact_bytes

ROOT = Path(__file__).resolve().parents[3]
REFERENCE_PYTHON = ROOT / "reference" / "python"
SCRIPT = REFERENCE_PYTHON / "scripts" / "build_engineering_rc_export_archive.py"


def test_two_builds_from_same_tree_produce_identical_archive_sha256(tmp_path: Path) -> None:
    first = build_engineering_rc_export_archive(ROOT, tmp_path / "first.zip", allow_non_runtime_output=True)
    second = build_engineering_rc_export_archive(ROOT, tmp_path / "second.zip", allow_non_runtime_output=True)

    assert first["ok"] is True
    assert second["ok"] is True
    assert first["archive_sha256"] == second["archive_sha256"]
    assert first["archive_size_bytes"] == second["archive_size_bytes"]


def test_verify_accepts_generated_archive(tmp_path: Path) -> None:
    archive = tmp_path / "rc.zip"
    build = build_engineering_rc_export_archive(ROOT, archive, allow_non_runtime_output=True)
    verify = verify_engineering_rc_export_archive(ROOT, archive)

    assert build["ok"] is True
    assert verify["ok"] is True
    assert verify["entry_count"] == build["entry_count"]


def test_archive_entry_list_exactly_matches_hash_manifest_artifacts(tmp_path: Path) -> None:
    archive = tmp_path / "rc.zip"
    build_engineering_rc_export_archive(ROOT, archive, allow_non_runtime_output=True)
    expected = _hash_manifest_paths()

    with zipfile.ZipFile(archive) as zf:
        names = zf.namelist()

    assert names == expected
    assert all("\\" not in name for name in names)


def test_rch1_archive_writes_canonical_lf_bytes_for_crlf_checkout_file(tmp_path: Path) -> None:
    archive = tmp_path / "rc.zip"
    path = "docs/roadmap/NOLLM_ENGINEERING_ROADMAP_V4_20260616.md"
    build = build_engineering_rc_export_archive(ROOT, archive, allow_non_runtime_output=True)

    with zipfile.ZipFile(archive) as zf:
        data = zf.read(path)

    assert build["ok"] is True, build["failures"]
    assert data == canonical_rc_artifact_bytes(ROOT, path)
    assert b"\r\n" not in data


def test_rch1_lf_and_crlf_fixture_archives_are_byte_identical(tmp_path: Path) -> None:
    repo_lf = _copy_archive_fixture(tmp_path / "lf")
    repo_crlf = _copy_archive_fixture(tmp_path / "crlf")
    path = repo_crlf / "docs/releases/NOLLM_ENGINEERING_GRAVITY_RC_AUDIT_20260618.md"
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    path.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))

    first = build_engineering_rc_export_archive(repo_lf, tmp_path / "lf.zip", allow_non_runtime_output=True)
    second = build_engineering_rc_export_archive(repo_crlf, tmp_path / "crlf.zip", allow_non_runtime_output=True)

    assert first["ok"] is True, first["failures"]
    assert second["ok"] is True, second["failures"]
    assert (tmp_path / "lf.zip").read_bytes() == (tmp_path / "crlf.zip").read_bytes()


def test_verifier_rejects_archive_with_unexpected_entry(tmp_path: Path) -> None:
    archive = tmp_path / "bad.zip"
    build_engineering_rc_export_archive(ROOT, archive, allow_non_runtime_output=True)
    with zipfile.ZipFile(archive, "a") as zf:
        zf.writestr("unexpected.txt", "not in manifest\n")

    report = verify_engineering_rc_export_archive(ROOT, archive)

    assert report["ok"] is False
    assert "archive_unexpected_entry:unexpected.txt" in report["failures"]


def test_verifier_rejects_backslash_and_path_traversal_entries(tmp_path: Path) -> None:
    archive = tmp_path / "bad_paths.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("bad/entry.txt", "bad\n")
        zf.writestr("../escape.txt", "bad\n")
    archive.write_bytes(archive.read_bytes().replace(b"bad/entry.txt", b"bad\\entry.txt"))

    report = verify_engineering_rc_export_archive(ROOT, archive)

    assert report["ok"] is False
    assert "archive_backslash_entry:bad\\entry.txt" in report["failures"]
    assert "archive_path_traversal_entry:../escape.txt" in report["failures"]


def test_builder_runtime_output_does_not_dirty_git_status() -> None:
    output = ROOT / "out/nollm_runtime/releases/h4_test_rc.zip"
    output.unlink(missing_ok=True)
    before = _git_status_short()
    result = run_subprocess(
        [sys.executable, str(SCRIPT), "--output", "../../out/nollm_runtime/releases/h4_test_rc.zip"],
        cwd=REFERENCE_PYTHON,
        timeout_seconds=30,
    )
    after = _git_status_short()

    assert result.returncode == 0, result.stdout + result.stderr
    assert before == after


def _hash_manifest_paths() -> list[str]:
    manifest = json.loads((ROOT / HASH_MANIFEST_PATH).read_text(encoding="utf-8"))
    return [item["path"] for item in manifest["artifacts"]]


def _copy_archive_fixture(target_root: Path) -> Path:
    target_root.mkdir(parents=True)
    manifest = build_engineering_rc_artifact_hash_manifest(ROOT)
    for item in manifest["artifacts"]:
        source = ROOT / item["path"]
        target = target_root / item["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    hash_target = target_root / HASH_MANIFEST_PATH
    hash_target.parent.mkdir(parents=True, exist_ok=True)
    hash_target.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target_root


def _git_status_short() -> str:
    result = run_subprocess(["git", "status", "--short"], cwd=ROOT, timeout_seconds=30)
    assert result.returncode == 0
    return result.stdout
