from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys

from subprocess_harness import run_subprocess
from nollm.engineering_rc_export import (
    HASH_MANIFEST_PATH,
    HASH_SCHEMA,
    build_engineering_rc_artifact_hash_manifest,
    build_engineering_rc_export_check,
    canonical_rc_artifact_bytes,
)

ROOT = Path(__file__).resolve().parents[3]
REFERENCE_PYTHON = ROOT / "reference" / "python"
SCRIPT = REFERENCE_PYTHON / "scripts" / "check_engineering_rc_export.py"


def test_hash_manifest_includes_required_rc_artifact_paths() -> None:
    manifest = _committed_hash_manifest()
    paths = {item["path"] for item in manifest["artifacts"]}

    assert manifest["schema"] == HASH_SCHEMA
    assert "docs/releases/NOLLM_ENGINEERING_GRAVITY_RC_AUDIT_20260618.md" in paths
    assert "docs/releases/NOLLM_ENGINEERING_GRAVITY_RC_EXPORT_MANIFEST_20260618.json" in paths
    assert "reference/python/scripts/check_engineering_rc_export.py" in paths
    assert "reference/python/tests/test_engineering_rc_artifact_hashes.py" in paths
    assert "out/nollm_runtime/g_series_engineering_closure_report.json" in paths


def test_hash_manifest_entries_are_sorted_and_deterministic() -> None:
    committed = _committed_hash_manifest()
    rebuilt = build_engineering_rc_artifact_hash_manifest(ROOT)
    paths = [item["path"] for item in committed["artifacts"]]

    assert paths == sorted(paths)
    assert committed == rebuilt
    assert committed["artifact_count"] == len(committed["artifacts"])


def test_hash_manifest_sha256_and_size_match_current_files() -> None:
    manifest = _committed_hash_manifest()

    for item in manifest["artifacts"]:
        data = canonical_rc_artifact_bytes(ROOT, item["path"])
        assert item["size_bytes"] == len(data)
        assert item["sha256"] == __import__("hashlib").sha256(data).hexdigest()


def test_rch1_roadmap_manifest_uses_canonical_lf_bytes() -> None:
    path = "docs/roadmap/NOLLM_ENGINEERING_ROADMAP_V4_20260616.md"
    manifest = _committed_hash_manifest()
    item = next(record for record in manifest["artifacts"] if record["path"] == path)
    data = canonical_rc_artifact_bytes(ROOT, path)

    assert b"\r\n" not in data
    assert item["size_bytes"] == len(data)
    assert item["sha256"] == __import__("hashlib").sha256(data).hexdigest()


def test_rch1_crlf_checkout_invariance_for_manifest_and_checker(tmp_path: Path) -> None:
    repo = _copy_hash_fixture(tmp_path)
    path = "docs/releases/NOLLM_ENGINEERING_GRAVITY_RC_AUDIT_20260618.md"
    target = repo / path
    lf_text = target.read_text(encoding="utf-8").replace("\r\n", "\n")
    lf_manifest = build_engineering_rc_artifact_hash_manifest(repo)
    target.write_bytes(lf_text.replace("\n", "\r\n").encode("utf-8"))
    crlf_manifest = build_engineering_rc_artifact_hash_manifest(repo)
    report = build_engineering_rc_export_check(repo)

    assert crlf_manifest == lf_manifest
    assert report["ok"] is True, report["failures"]


def test_checker_fails_on_corrupted_file_in_temp_copy(tmp_path: Path) -> None:
    repo = _copy_hash_fixture(tmp_path)
    audit = repo / "docs/releases/NOLLM_ENGINEERING_GRAVITY_RC_AUDIT_20260618.md"
    audit.write_text(audit.read_text(encoding="utf-8") + "\ncorrupted\n", encoding="utf-8")

    result = run_subprocess(
        [sys.executable, str(SCRIPT), "--repo-root", str(repo)],
        cwd=REFERENCE_PYTHON,
        timeout_seconds=30,
    )
    report = json.loads(result.stdout)

    assert result.returncode == 1
    assert "hash_manifest_sha256_mismatch:docs/releases/NOLLM_ENGINEERING_GRAVITY_RC_AUDIT_20260618.md" in report[
        "failures"
    ]
    assert "hash_manifest_size_mismatch:docs/releases/NOLLM_ENGINEERING_GRAVITY_RC_AUDIT_20260618.md" in report[
        "failures"
    ]


def test_rch1_bare_cr_artifact_is_rejected(tmp_path: Path) -> None:
    repo = _copy_hash_fixture(tmp_path)
    path = "docs/releases/NOLLM_ENGINEERING_GRAVITY_RC_AUDIT_20260618.md"
    (repo / path).write_bytes(b"line one\rline two\n")

    report = build_engineering_rc_export_check(repo)

    assert report["ok"] is False
    assert f"bare_cr_in_rc_artifact:{path}" in report["failures"]


def test_rch1_unsupported_canonical_suffix_is_rejected(tmp_path: Path) -> None:
    binary = tmp_path / "repo" / "docs" / "artifact.bin"
    binary.parent.mkdir(parents=True)
    binary.write_bytes(b"\x00\x01")

    try:
        canonical_rc_artifact_bytes(tmp_path / "repo", "docs/artifact.bin")
    except ValueError as exc:
        assert str(exc) == "unsupported_rc_artifact_suffix:docs/artifact.bin"
    else:
        raise AssertionError("unsupported RC artifact suffix was accepted")


def test_ignored_local_paths_are_excluded_even_when_present(tmp_path: Path) -> None:
    repo = _copy_hash_fixture(tmp_path)
    (repo / "conversation_backups").mkdir()
    (repo / "conversation_backups" / "local.txt").write_text("local only\n", encoding="utf-8")
    (repo / "reference/python/nollm/__pycache__").mkdir()
    (repo / "reference/python/nollm/__pycache__" / "local.pyc").write_bytes(b"cache")

    result = run_subprocess(
        [sys.executable, str(SCRIPT), "--repo-root", str(repo)],
        cwd=REFERENCE_PYTHON,
        timeout_seconds=30,
    )
    report = json.loads(result.stdout)
    payload = json.dumps(report, sort_keys=True)

    assert result.returncode == 0, report["failures"]
    assert report["ok"] is True
    assert "conversation_backups/local.txt" not in payload
    assert "__pycache__/local.pyc" not in payload


def test_checker_remains_clean_after_runtime_cache_artifacts_are_created_and_removed(tmp_path: Path) -> None:
    cache_dir = ROOT / "reference/python/nollm/__pycache__"
    cache_file = cache_dir / "h3_cache_probe.pyc"
    before = _git_status_short()
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file.write_bytes(b"cache")
        result = run_subprocess(
            [sys.executable, str(SCRIPT)],
            cwd=REFERENCE_PYTHON,
            timeout_seconds=30,
        )
        cache_file.unlink()
    finally:
        if cache_file.exists():
            cache_file.unlink()
        if cache_dir.exists() and not any(cache_dir.iterdir()):
            cache_dir.rmdir()
    after = _git_status_short()

    assert result.returncode == 0, result.stdout + result.stderr
    assert before == after


def _committed_hash_manifest() -> dict[str, object]:
    return json.loads((ROOT / HASH_MANIFEST_PATH).read_text(encoding="utf-8"))


def _copy_hash_fixture(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    manifest = build_engineering_rc_artifact_hash_manifest(ROOT)
    for item in manifest["artifacts"]:
        source = ROOT / item["path"]
        target = repo / item["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    hash_target = repo / HASH_MANIFEST_PATH
    hash_target.parent.mkdir(parents=True, exist_ok=True)
    hash_target.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return repo


def _git_status_short() -> str:
    result = run_subprocess(["git", "status", "--short"], cwd=ROOT, timeout_seconds=30)
    assert result.returncode == 0
    return result.stdout
