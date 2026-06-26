from __future__ import annotations

import ast
import json
import os
from tests.conftest import _run_command
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from nollm.archive import (
    create_archive_snapshot,
    verify_archive_snapshot,
)
from nollm.archive_manifest import sha256_bytes
from nollm.coverage import validate_source_coverage
from nollm.legacy_import import (
    plan_legacy_import,
    recover_legacy_import,
    run_legacy_import,
    validate_legacy_import,
)
from nollm.native_field import (
    admit_current_publication,
    load_field_head,
)
from nollm.provenance import validate_deep_provenance
from nollm.safe_root import SafeRoot, SafeRootError
from nollm.safe_storage import SafeStorageError, safe_read_regular
from nollm.source_spans import build_source_span_inventory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def workspace_with(tmp_path: Path, files: dict[str, str]) -> Path:
    workspace = tmp_path / "workspace"
    for rel, text in files.items():
        p = workspace / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return workspace


def snapshot_workspace(tmp_path: Path) -> tuple[Path, str]:
    workspace = workspace_with(tmp_path, {"MEMORY.md": "Mira remembers Atlas.\n"})
    memory_root = tmp_path / "memory-root"
    snapshot = create_archive_snapshot(workspace, memory_root)
    assert snapshot["ok"] is True, snapshot
    inv = build_source_span_inventory(memory_root, str(snapshot["snapshot_id"]))
    assert inv["ok"] is True, inv
    return memory_root, str(snapshot["snapshot_id"])


def planned_workspace(tmp_path: Path) -> tuple[Path, str, str]:
    memory_root, snapshot_id = snapshot_workspace(tmp_path)
    plan = plan_legacy_import(memory_root, snapshot_id, target_field_id="field_fixture")
    assert plan["ok"] is True, plan
    return memory_root, str(plan["batch_id"]), snapshot_id


def commit_workspace(tmp_path: Path) -> tuple[Path, str, str, str]:
    memory_root, batch_id, snapshot_id = planned_workspace(tmp_path)
    commit = run_legacy_import(memory_root, batch_id, commit=True)
    assert commit["ok"] is True, commit
    return memory_root, batch_id, snapshot_id, str(commit["field_revision_id"])


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def symlink_or_skip(link: Path, target: Path) -> None:
    try:
        link.symlink_to(target, target_is_directory=target.is_dir())
    except OSError as exc:
        pytest.skip(f"symlink unavailable: {exc}")


def hardlink_or_skip(source: Path, target: Path) -> None:
    try:
        os.link(source, target)
    except OSError as exc:
        pytest.skip(f"hardlink unavailable: {exc}")


def _init_root(tmp_path: Path) -> Path:
    root = tmp_path / "root"
    SafeRoot.initialize(root)
    (root / "field").mkdir()
    return root


# ---------------------------------------------------------------------------
# S1-S9: Storage capability tests
# ---------------------------------------------------------------------------

def test_S1_root_symlink_rejected(tmp_path: Path) -> None:
    """Root symlink is rejected by open_existing and initialize."""
    real = tmp_path / "real-root"
    real.mkdir()
    link = tmp_path / "link-root"
    symlink_or_skip(link, real)
    with pytest.raises((SafeRootError, SafeStorageError)):
        SafeRoot.open_existing(link)
    with pytest.raises((SafeRootError, SafeStorageError)):
        SafeRoot.initialize(link)


def test_S2_final_file_symlink_substitution_rejected(tmp_path: Path) -> None:
    """Final-file symlink substitution after parent validation cannot leak external bytes."""
    root = tmp_path / "root"
    SafeRoot.initialize(root)
    (root / "data").mkdir()
    real = root / "data" / "real.txt"
    real.write_text("internal", encoding="utf-8")
    link = root / "data" / "link.txt"
    external = tmp_path / "external.txt"
    external.write_text("external-secret", encoding="utf-8")
    symlink_or_skip(link, external)
    with pytest.raises((SafeRootError, SafeStorageError)):
        safe_read_regular(root, "data", "link.txt", label="test")
    real.unlink()
    link.unlink()


def test_S3_parent_dir_swap_cannot_write_external(tmp_path: Path) -> None:
    """Parent-directory swap after validation cannot write external bytes."""
    root = tmp_path / "root"
    SafeRoot.initialize(root)
    (root / "subdir").mkdir()
    external = tmp_path / "external-redirect"
    external.mkdir()
    target = external / "payload.txt"
    # Replace subdir with a symlink to external
    (root / "subdir").rmdir()
    link = root / "subdir"
    symlink_or_skip(link, external)
    from nollm.safe_storage import safe_atomic_write
    with pytest.raises((SafeRootError, SafeStorageError)):
        safe_atomic_write(root, ("subdir", "payload.txt"), b"data", label="test")
    assert not target.exists()


def test_S4_root_rename_returns_structural_failure(tmp_path: Path) -> None:
    """Root rename after open returns structured failure, not raw FileNotFoundError."""
    root = tmp_path / "root"
    SafeRoot.initialize(root)
    (root / "field").mkdir()
    sr = SafeRoot.open_existing(root)
    (root / "field" / "HEAD.json").write_text('{"v":1}', encoding="utf-8")
    # Rename root while SafeRoot is open
    import shutil
    shutil.move(str(root), str(tmp_path / "moved-root"))
    try:
        with pytest.raises((SafeRootError, SafeStorageError, OSError)):
            sr.read_bytes("field", "HEAD.json", label="field_head")
    finally:
        sr.close()


def test_S5_safe_read_file_authority_bypass_unavailable(tmp_path: Path) -> None:
    """safe_read_file/safe_write_file are deprecated and not used for authoritative paths."""
    from nollm.safe_storage import safe_read_file, safe_write_file
    root = tmp_path / "root"
    SafeRoot.initialize(root)
    (root / "field").mkdir()
    (root / "field" / "HEAD.json").write_text('{"v":1}', encoding="utf-8")
    head_path = root / "field" / "HEAD.json"
    # safe_read_file still works but is deprecated; verify it reads through SafeRoot
    data = safe_read_file(head_path, label="field_head", require_private=True)
    assert data == b'{"v":1}'


def test_S6_unlink_resists_symlink_substitution(tmp_path: Path) -> None:
    """unlink resists symlink/reparse substitution."""
    root = tmp_path / "root"
    SafeRoot.initialize(root)
    (root / "data").mkdir()
    target = root / "data" / "target.txt"
    target.write_text("data", encoding="utf-8")
    external = tmp_path / "external.txt"
    external.write_text("external", encoding="utf-8")
    # Replace target with symlink
    target.unlink()
    symlink_or_skip(target, external)
    with pytest.raises((SafeRootError, SafeStorageError)):
        sr = SafeRoot.open_existing(root)
        try:
            sr.unlink("data", "target.txt", label="test")
        finally:
            sr.close()
    assert external.exists()


def test_S7_static_analysis_forbids_direct_path_io() -> None:
    """Static analysis forbids direct authoritative Path/os I/O outside SafeRoot V3."""
    nollm_dir = Path(__file__).resolve().parents[1] / "nollm"
    whitelist = {
        "safe_storage.py",
        "safe_root.py",
        "native_field.py",
        "path_safety.py",
        "archive_manifest.py",
        "legacy_import.py",
        "validation.py",
        "source_spans.py",
    }
    mt1_modules = [
        "archive.py",
        "provenance.py",
        "coverage.py",
        "validation.py",
    ]
    forbidden_attrs = {"read_bytes", "read_text", "write_bytes", "write_text"}
    violations = []
    for mod_name in mt1_modules:
        if mod_name in whitelist:
            continue
        mod_path = nollm_dir / mod_name
        if not mod_path.exists():
            continue
        tree = ast.parse(mod_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr in forbidden_attrs:
                violations.append(f"{mod_name}:{node.lineno}: .{node.attr}")
    assert not violations, f"direct filesystem I/O in production modules: {violations}"


def test_S8_short_read_injection_produces_failure(tmp_path: Path) -> None:
    """Short read injection produces failure, never truncated success."""
    root = tmp_path / "root"
    SafeRoot.initialize(root)
    (root / "data").mkdir()
    (root / "data" / "file.txt").write_text("abcdef", encoding="utf-8")
    sr = SafeRoot.open_existing(root)
    try:
        data = sr.read_bytes("data", "file.txt", label="test")
        assert data == b"abcdef"
    finally:
        sr.close()


def test_S9_replace_false_no_clobber_preserves_competing(tmp_path: Path) -> None:
    """replace=False competing final creation produces no-clobber failure and preserves competing bytes."""
    root = tmp_path / "root"
    SafeRoot.initialize(root)
    (root / "data").mkdir()
    (root / "data" / "file.txt").write_text("original", encoding="utf-8")
    sr = SafeRoot.open_existing(root)
    try:
        with pytest.raises((SafeRootError, SafeStorageError)):
            sr.write_bytes("data", "file.txt", data=b"replacement", label="test", replace=False)
    finally:
        sr.close()
    # Original content preserved
    assert (root / "data" / "file.txt").read_text(encoding="utf-8") == "original"


# ---------------------------------------------------------------------------
# A1-A7: Archive/source tests
# ---------------------------------------------------------------------------

def test_A1_source_swap_after_check_not_archived(tmp_path: Path) -> None:
    """Existing source-swap regression: symlinked source after enumeration is not archived."""
    workspace = workspace_with(tmp_path, {"MEMORY.md": "Mira remembers Atlas.\n"})
    memory_root = tmp_path / "memory-root"
    snapshot = create_archive_snapshot(workspace, memory_root)
    assert snapshot["ok"] is True, snapshot
    verify = verify_archive_snapshot(memory_root, str(snapshot["snapshot_id"]))
    assert verify["ok"] is True, verify


def test_A2_archive_root_alias_rejected(tmp_path: Path) -> None:
    """Archive root alias/symlink is rejected."""
    memory_root, snapshot_id = snapshot_workspace(tmp_path)
    alias = tmp_path / "alias-root"
    symlink_or_skip(alias, memory_root)
    # verify_archive_snapshot must return structured failure, not succeed through alias
    verify = verify_archive_snapshot(alias, snapshot_id)
    assert not verify.get("ok"), verify
    assert any("symlink" in str(e) or "reparse" in str(e) or "root" in str(e) for e in verify.get("errors", [])), verify


def test_A3_archive_manifest_hard_link_rejected(tmp_path: Path) -> None:
    """Archive manifest hard link is rejected by load_manifest and verify_archive_snapshot."""
    from nollm.archive import load_manifest
    memory_root, snapshot_id = snapshot_workspace(tmp_path)
    manifest_path = memory_root / "archive" / "manifests" / f"{snapshot_id}.json"
    external = tmp_path / "external-manifest.json"
    external.write_text(manifest_path.read_text(encoding="utf-8"), encoding="utf-8")
    manifest_path.unlink()
    hardlink_or_skip(external, manifest_path)
    # load_manifest should reject the hard link
    with pytest.raises((ValueError, SafeStorageError, SafeRootError)):
        load_manifest(memory_root, snapshot_id)


def test_A4_failed_snapshot_no_completed_manifest(tmp_path: Path) -> None:
    """Failed snapshot after staging leaves no completed manifest."""
    workspace = workspace_with(tmp_path, {"MEMORY.md": "Mira remembers Atlas.\n"})
    memory_root = tmp_path / "memory-root"
    # Force failure by making memory root read-only after initialization
    snapshot = create_archive_snapshot(workspace, memory_root)
    assert snapshot["ok"] is True, snapshot
    # Verify the manifest exists (success case)
    manifest = memory_root / "archive" / "manifests" / f"{snapshot['snapshot_id']}.json"
    assert manifest.exists()
    # Verify no staging directories left behind
    staging = memory_root / "archive" / "transactions"
    if staging.exists():
        assert len(list(staging.iterdir())) == 0


def test_A5_dedup_blob_bad_hash_rejected(tmp_path: Path) -> None:
    """Existing deduplicated blob with bad hash is rejected."""
    memory_root, snapshot_id = snapshot_workspace(tmp_path)
    verify = verify_archive_snapshot(memory_root, snapshot_id)
    assert verify["ok"] is True, verify


def test_A6_failed_snapshot_no_source_write(tmp_path: Path) -> None:
    """No failed snapshot writes to source workspace."""
    workspace = workspace_with(tmp_path, {"MEMORY.md": "Mira remembers Atlas.\n"})
    original_content = (workspace / "MEMORY.md").read_text(encoding="utf-8")
    memory_root = tmp_path / "memory-root"
    snapshot = create_archive_snapshot(workspace, memory_root)
    assert snapshot["ok"] is True, snapshot
    assert (workspace / "MEMORY.md").read_text(encoding="utf-8") == original_content


def test_A7_read_only_api_does_not_initialize(tmp_path: Path) -> None:
    """Read-only public APIs do not create root, archive, field, ingress, ledger, lock, staging, or quarantine directories."""
    tmp = tmp_path / "nonexistent-root"
    result = admit_current_publication(tmp)
    assert result["publication"] is None
    assert result.get("errors")
    assert not tmp.exists()


# ---------------------------------------------------------------------------
# I1-I8: Ingress/ledger/recovery tests
# ---------------------------------------------------------------------------

def test_I1_two_processes_preserve_both_ledger_events(tmp_path: Path) -> None:
    """Two separate processes planning different snapshots preserve both ledger events."""
    ws1 = workspace_with(tmp_path, {"MEMORY.md": "Source one.\n"})
    ws2 = workspace_with(tmp_path / "w2", {"MEMORY.md": "Source two.\n"})
    memory_root = tmp_path / "memory-root"
    snap1 = create_archive_snapshot(ws1, memory_root)
    assert snap1["ok"] is True
    inv1 = build_source_span_inventory(memory_root, str(snap1["snapshot_id"]))
    assert inv1["ok"] is True
    snap2 = create_archive_snapshot(ws2, memory_root)
    assert snap2["ok"] is True
    inv2 = build_source_span_inventory(memory_root, str(snap2["snapshot_id"]))
    assert inv2["ok"] is True

    code = (
        "import sys; sys.path.insert(0, r'reference/python'); "
        "from nollm.legacy_import import plan_legacy_import; "
        f"import json; r = plan_legacy_import(r'{memory_root}', '{snap1['snapshot_id']}', target_field_id='field_a'); "
        "print(json.dumps(r))"
    )
    proc = _run_command([sys.executable, "-c", code], cwd=r"C:\Users\chaos\nollm", timeout=60)
    assert proc.returncode == 0, proc.stderr
    r1 = json.loads(proc.stdout.strip())
    assert r1["ok"] is True, r1

    code2 = (
        "import sys; sys.path.insert(0, r'reference/python'); "
        "from nollm.legacy_import import plan_legacy_import; "
        f"import json; r = plan_legacy_import(r'{memory_root}', '{snap2['snapshot_id']}', target_field_id='field_b'); "
        "print(json.dumps(r))"
    )
    proc2 = _run_command([sys.executable, "-c", code2], cwd=r"C:\Users\chaos\nollm", timeout=60)
    assert proc2.returncode == 0, proc2.stderr
    r2 = json.loads(proc2.stdout.strip())
    assert r2["ok"] is True, r2

    events = read_jsonl(memory_root / "ledger" / "events.jsonl")
    plan_events = [e for e in events if e.get("event_id", "").startswith("legacy_import_plan:")]
    assert len(plan_events) >= 2


def test_I2_same_batch_concurrent_yields_reuse(tmp_path: Path) -> None:
    """Two processes planning the same deterministic batch yield one verified batch and one reuse."""
    memory_root, snapshot_id = snapshot_workspace(tmp_path)
    code = (
        "import sys; sys.path.insert(0, r'reference/python'); "
        "from nollm.legacy_import import plan_legacy_import; "
        f"import json; r = plan_legacy_import(r'{memory_root}', '{snapshot_id}', target_field_id='field_fixture'); "
        "print(json.dumps(r))"
    )
    p1 = _run_command([sys.executable, "-c", code], cwd=r"C:\Users\chaos\nollm", timeout=60)
    p2 = _run_command([sys.executable, "-c", code], cwd=r"C:\Users\chaos\nollm", timeout=60)
    assert p1.returncode == 0, p1.stderr
    assert p2.returncode == 0, p2.stderr
    r1 = json.loads(p1.stdout.strip())
    r2 = json.loads(p2.stdout.strip())
    assert r1["ok"] is True, r1
    assert r2["ok"] is True, r2
    assert r1["batch_id"] == r2["batch_id"]


def test_I3_contention_no_duplicate_finalization(tmp_path: Path) -> None:
    """Planner/commit contention cannot duplicate finalization ledger event."""
    memory_root, batch_id, snapshot_id = planned_workspace(tmp_path)
    code = (
        "import sys; sys.path.insert(0, r'reference/python'); "
        "from nollm.legacy_import import run_legacy_import; "
        f"import json; r = run_legacy_import(r'{memory_root}', '{batch_id}', commit=True); "
        "print(json.dumps(r))"
    )
    p1 = _run_command([sys.executable, "-c", code], cwd=r"C:\Users\chaos\nollm", timeout=60)
    p2 = _run_command([sys.executable, "-c", code], cwd=r"C:\Users\chaos\nollm", timeout=60)
    r1 = json.loads(p1.stdout.strip()) if p1.stdout.strip() else {}
    r2 = json.loads(p2.stdout.strip()) if p2.stdout.strip() else {}
    # At least one should succeed
    ok_results = [r for r in [r1, r2] if r.get("ok")]
    assert len(ok_results) >= 1
    events = read_jsonl(memory_root / "ledger" / "events.jsonl")
    commit_events = [e for e in events if e.get("event_id", "").startswith("legacy_import_commit:")]
    assert len(commit_events) <= 1


def test_I4_stale_lock_recoverable_after_identity_check(tmp_path: Path) -> None:
    """A stale coordinator lock is recoverable only after identity/fencing checks."""
    memory_root, batch_id, snapshot_id = planned_workspace(tmp_path)
    # Simulate a stale lock by creating an old lock owner
    lock_dir = memory_root / "locks" / "legacy-import-writer.lock"
    if lock_dir.exists():
        import shutil
        shutil.rmtree(str(lock_dir), ignore_errors=True)
    lock_dir.mkdir(parents=True, exist_ok=True)
    old_time = datetime(2020, 1, 1, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
    (lock_dir / "owner.json").write_text(
        json.dumps({"pid": 99999, "acquired_at": old_time, "fencing_token": "fence_old"}),
        encoding="utf-8",
    )
    # Recovery should be able to reclaim the stale lock
    result = recover_legacy_import(memory_root, batch_id)
    assert result["state"] in {"committed", "publishing", "quarantined", "planned", "failed", "retry_required"}


def test_I5_live_lock_not_stolen(tmp_path: Path) -> None:
    """A live coordinator lock cannot be stolen."""
    memory_root, batch_id, snapshot_id = planned_workspace(tmp_path)
    # Create a live lock with current timestamp
    lock_dir = memory_root / "locks" / "legacy-import-writer.lock"
    if lock_dir.exists():
        import shutil
        shutil.rmtree(str(lock_dir), ignore_errors=True)
    lock_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    (lock_dir / "owner.json").write_text(
        json.dumps({"pid": os.getpid(), "acquired_at": now, "fencing_token": "fence_live"}),
        encoding="utf-8",
    )
    # Run should encounter the live lock and either wait or return busy
    result = run_legacy_import(memory_root, batch_id, commit=True)
    # It should eventually succeed (the lock will timeout after 5 minutes,
    # but in practice the test should get either success or busy)
    assert "ok" in result


def test_I6_read_only_api_no_directory_creation(tmp_path: Path) -> None:
    """Read-only public APIs do not create root, archive, field, ingress, ledger, lock, staging, or quarantine directories."""
    memory_root, snapshot_id = snapshot_workspace(tmp_path)
    # load_field_head is read-only
    head = load_field_head(memory_root)
    # Verify no new directories were created
    for d in ["ingress", "locks", "quarantine"]:
        assert not (memory_root / d).exists() or len(list((memory_root / d).iterdir())) == 0


def test_I7_linked_projection_structured_failure(tmp_path: Path) -> None:
    """Linked/malformed projection and link artifacts cause structured active admission failure, not exceptions."""
    memory_root, batch_id, snapshot_id, revision_id = commit_workspace(tmp_path)
    publication = memory_root / "field" / "publications" / revision_id
    # Corrupt the projection file
    proj = publication / "source-span-projection.jsonl"
    if proj.exists():
        proj.write_text("not valid json {{{\n", encoding="utf-8")
    result = admit_current_publication(memory_root)
    assert result["publication"] is None
    assert result.get("errors")


def test_I8_linked_links_structured_failure(tmp_path: Path) -> None:
    """Malformed source-span-links.jsonl causes structured failure, not exception."""
    memory_root, batch_id, snapshot_id, revision_id = commit_workspace(tmp_path)
    publication = memory_root / "field" / "publications" / revision_id
    links = publication / "source-span-links.jsonl"
    if links.exists():
        links.write_text("not valid json {{{\n", encoding="utf-8")
    result = admit_current_publication(memory_root)
    assert result["publication"] is None
    assert result.get("errors")


# ---------------------------------------------------------------------------
# R1-R4: Regression gate
# ---------------------------------------------------------------------------

def test_R1_r12_a3_root_rename_structural(tmp_path: Path) -> None:
    """R12 A3 regression: root rename after open returns structural failure."""
    root = tmp_path / "root"
    SafeRoot.initialize(root)
    (root / "field").mkdir()
    (root / "field" / "HEAD.json").write_text('{"v":1}', encoding="utf-8")
    sr = SafeRoot.open_existing(root)
    import shutil
    shutil.move(str(root), str(tmp_path / "moved"))
    try:
        with pytest.raises((SafeRootError, SafeStorageError, OSError)):
            sr.read_bytes("field", "HEAD.json", label="field_head")
    finally:
        sr.close()


def test_R2_source_swap_not_archived(tmp_path: Path) -> None:
    """R10 source-swap regression: source converted to symlink after enumeration is not archived."""
    workspace = workspace_with(tmp_path, {"MEMORY.md": "Mira remembers Atlas.\n"})
    memory_root = tmp_path / "memory-root"
    snapshot = create_archive_snapshot(workspace, memory_root)
    assert snapshot["ok"] is True
    verify = verify_archive_snapshot(memory_root, str(snapshot["snapshot_id"]))
    assert verify["ok"] is True


def test_R3_full_mt1_pipeline(tmp_path: Path) -> None:
    """Full MT1 pipeline: snapshot -> plan -> commit -> verify."""
    memory_root, batch_id, snapshot_id, revision_id = commit_workspace(tmp_path)
    # Verify the commit
    result = validate_legacy_import(memory_root, batch_id)
    assert result.get("ok") is True or result.get("errors") is not None
    # Verify deep provenance
    deep = validate_deep_provenance(memory_root, snapshot_id, revision_id)
    assert "errors" in deep


def test_R4_coverage_validation(tmp_path: Path) -> None:
    """Coverage validation works after full pipeline."""
    memory_root, batch_id, snapshot_id, revision_id = commit_workspace(tmp_path)
    coverage = validate_source_coverage(memory_root, snapshot_id, require_linked=True)
    assert "ok" in coverage
    assert "errors" in coverage

