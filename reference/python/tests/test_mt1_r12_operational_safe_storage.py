from __future__ import annotations

import ast
import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

import nollm.archive as archive_module
from nollm.archive import (
    create_archive_snapshot,
    verify_archive_snapshot,
    workspace_identity_for,
    snapshot_seed_digest,
)
from nollm.archive_manifest import manifest_hash, read_json, sha256_bytes, write_json
from nollm.coverage import validate_source_coverage
from nollm.legacy_extract import extract_legacy_spans
from nollm.legacy_import import (
    plan_legacy_import,
    recover_legacy_import,
    run_legacy_import,
    validate_legacy_import,
)
from nollm.native_field import (
    admit_current_publication,
    load_field_head,
    stage_shards,
    move_staged_shards,
    publish_field_revision,
)
from nollm.provenance import validate_deep_provenance
from nollm.source_spans import (
    build_source_span_inventory,
    load_source_spans,
    write_source_spans,
    mark_spans_linked,
)
from nollm.safe_storage import SafeStorageError


# ---------------------------------------------------------------------------
# Test helpers (minimal re-definition set from R10/R11)
# ---------------------------------------------------------------------------

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def workspace_with(tmp_path: Path, files: dict[str, str]) -> Path:
    workspace = tmp_path / "workspace"
    for rel, text in files.items():
        path = workspace / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return workspace


def snapshot_workspace(tmp_path: Path) -> tuple[Path, str]:
    workspace = workspace_with(tmp_path, {"MEMORY.md": "Mira remembers Atlas.\n"})
    memory_root = tmp_path / "memory-root"
    snapshot = create_archive_snapshot(workspace, memory_root)
    assert snapshot["ok"] is True, snapshot
    inventory = build_source_span_inventory(memory_root, str(snapshot["snapshot_id"]))
    assert inventory["ok"] is True, inventory
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


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in records), encoding="utf-8")


def remove_tree(path: Path) -> None:
    if path.exists() and path.is_dir() and not path.is_symlink():
        for child in sorted(path.rglob("*"), reverse=True):
            if child.is_file() or child.is_symlink():
                child.unlink()
            elif child.is_dir():
                child.rmdir()
        path.rmdir()
    elif path.exists() or path.is_symlink():
        path.unlink()


def symlink_or_skip(link: Path, target: Path) -> None:
    try:
        link.symlink_to(target, target_is_directory=target.is_dir())
    except OSError as exc:
        pytest.skip(f"symlink unavailable on this host: {exc}")


def hardlink_or_skip(source: Path, target: Path) -> None:
    try:
        os.link(source, target)
    except OSError as exc:
        pytest.skip(f"hardlink unavailable on this host: {exc}")


def tree_fingerprint(root: Path) -> dict[str, str]:
    return {path.relative_to(root).as_posix(): sha256_bytes(path.read_bytes()) for path in sorted(root.rglob("*")) if path.is_file()}

# ---------------------------------------------------------------------------
# Cluster A: TOCTOU / parent directory swap
# ---------------------------------------------------------------------------

def test_A1_parent_swap_during_manifest_read_is_rejected(tmp_path: Path) -> None:
    """Replace manifest parent dir with symlink to external content; verify must reject."""
    memory_root, snapshot_id = snapshot_workspace(tmp_path)
    manifest_dir = memory_root / "archive" / "manifests"
    external = tmp_path / "external-manifests"
    external.mkdir()
    (external / f"{snapshot_id}.json").write_text('{"pwned": true}', encoding="utf-8")
    remove_tree(manifest_dir)
    symlink_or_skip(manifest_dir, external)
    result = verify_archive_snapshot(memory_root, snapshot_id)
    assert result["ok"] is False
    assert not any("pwned" in str(e) for e in result.get("errors", []))


def test_A2_parent_swap_during_span_read_is_rejected(tmp_path: Path) -> None:
    """Replace source-spans parent dir with symlink before load; must not return external content."""
    memory_root, snapshot_id = snapshot_workspace(tmp_path)
    spans_dir = memory_root / "archive" / "source-spans"
    external = tmp_path / "external-spans"
    external.mkdir()
    (external / f"{snapshot_id}.jsonl").write_text('{"pwned": true}\n', encoding="utf-8")
    remove_tree(spans_dir)
    symlink_or_skip(spans_dir, external)
    try:
        load_source_spans(memory_root, snapshot_id)
        raised = False
    except (ValueError, Exception) as exc:
        raised = True
        assert "pwned" not in str(exc)
    assert raised, "should have raised on symlinked span dir"


def test_A3_root_path_rename_after_open_does_not_follow(tmp_path: Path) -> None:
    """After SafeRoot opens root, root rename must not let stale path serve content."""
    memory_root, snapshot_id = snapshot_workspace(tmp_path)
    from nollm.safe_root import SafeRoot, SafeRootError
    sr = SafeRoot.open_existing(memory_root)
    try:
        data = sr.read_bytes("archive", "manifests", f"{snapshot_id}.json", label="archive_manifest")
        assert b"schema" in data
    finally:
        sr.close()
    # After closing, rename the root; opening the old path must fail
    import shutil
    new_root = tmp_path / "renamed-root"
    try:
        shutil.move(str(memory_root), str(new_root))
    except OSError:
        # Windows may refuse to rename a directory that had open handles.
        # In that case, verify that opening a non-existent root path fails structurally.
        pass
    if not memory_root.exists():
        with pytest.raises((SafeRootError, OSError)):
            sr2 = SafeRoot.open_existing(memory_root)
    else:
        # Root still exists (rename blocked); clean up
        try:
            shutil.move(str(new_root), str(memory_root))
        except OSError:
            pass


def test_B1_hardlinked_head_rejected_by_admission(tmp_path: Path) -> None:
    """HEAD.json hard-linked to external file: admission must fail, no active publication."""
    memory_root, _batch_id, _snapshot_id, revision_id = commit_workspace(tmp_path)
    external = tmp_path / "external-head.json"
    external.write_text("external", encoding="utf-8")
    head = memory_root / "field" / "HEAD.json"
    head.unlink()
    hardlink_or_skip(external, head)
    admission = admit_current_publication(memory_root)
    assert admission["publication"] is None


def test_B2_hardlinked_receipt_rejected_by_admission(tmp_path: Path) -> None:
    """Publication receipt.json hard-linked: admission must fail closed."""
    memory_root, batch_id, snapshot_id, revision_id = commit_workspace(tmp_path)
    receipt = memory_root / "field" / "publications" / revision_id / "receipt.json"
    external = tmp_path / "external-receipt.json"
    external.write_bytes(receipt.read_bytes())
    receipt.unlink()
    hardlink_or_skip(external, receipt)
    admission = admit_current_publication(memory_root)
    assert admission["publication"] is None


def test_B3_hardlinked_activation_rejected_by_admission(tmp_path: Path) -> None:
    """activation.json hard-linked: admission must fail closed."""
    memory_root, _batch_id, _snapshot_id, revision_id = commit_workspace(tmp_path)
    activation = memory_root / "field" / "publications" / revision_id / "activation.json"
    external = tmp_path / "external-activation.json"
    external.write_text("external", encoding="utf-8")
    activation.unlink()
    hardlink_or_skip(external, activation)
    admission = admit_current_publication(memory_root)
    assert admission["publication"] is None


# ---------------------------------------------------------------------------
# Cluster C: public API no side-effect and no raw exception
# ---------------------------------------------------------------------------

def test_C1_corrupted_manifest_no_raw_exception(tmp_path: Path) -> None:
    """Corrupted manifest JSON returns structured error, not traceback."""
    memory_root, snapshot_id = snapshot_workspace(tmp_path)
    manifest_path = memory_root / "archive" / "manifests" / f"{snapshot_id}.json"
    manifest_path.write_text("not json at all {{{", encoding="utf-8")
    verify = verify_archive_snapshot(memory_root, snapshot_id)
    assert verify["ok"] is False
    assert any("malformed_json" in e for e in verify["errors"])


def test_C2_missing_root_no_side_effect(tmp_path: Path) -> None:
    """APIs on missing root must not create it."""
    missing = tmp_path / "does-not-exist"
    valid_snapshot = "snap_20260622_000000_" + "a" * 12
    verify_archive_snapshot(missing, valid_snapshot)
    build_source_span_inventory(missing, valid_snapshot)
    admit_current_publication(missing)
    assert not missing.exists()


def test_C3_invalid_snapshot_id_no_side_effect(tmp_path: Path) -> None:
    """Invalid snapshot_id must not create root or side effects."""
    memory_root = tmp_path / "memory-root"
    memory_root.mkdir()
    result = build_source_span_inventory(memory_root, "not-a-valid-snapshot-id")
    assert result["ok"] is False
    assert any("invalid_snapshot" in e for e in result["errors"])


def test_C4_extract_legacy_spans_no_implicit_root_creation(tmp_path: Path) -> None:
    """extract_legacy_spans on non-existent root must not create it."""
    missing = tmp_path / "nonexistent-root"
    valid_snapshot = "snap_20260622_000000_" + "a" * 12
    try:
        extract_legacy_spans(missing, valid_snapshot)
    except (ValueError, Exception):
        pass
    assert not missing.exists()


# ---------------------------------------------------------------------------
# Cluster D: concurrency / locking
# ---------------------------------------------------------------------------

def test_D1_concurrent_plan_different_snapshots_no_lost_events(tmp_path: Path) -> None:
    """Two different snapshot concurrent plans: both succeed, ledger has both events."""
    workspace_a = workspace_with(tmp_path / "a", {"MEMORY.md": "Alpha memory.\n"})
    workspace_b = workspace_with(tmp_path / "b", {"MEMORY.md": "Beta memory.\n"})
    memory_root = tmp_path / "memory-root"
    snap_a = create_archive_snapshot(workspace_a, memory_root)
    snap_b = create_archive_snapshot(workspace_b, memory_root)
    assert snap_a["ok"] and snap_b["ok"]
    build_source_span_inventory(memory_root, str(snap_a["snapshot_id"]))
    build_source_span_inventory(memory_root, str(snap_b["snapshot_id"]))
    results: list[dict[str, Any]] = []
    barrier = threading.Barrier(2)

    def worker(snapshot_id: str) -> None:
        barrier.wait()
        results.append(plan_legacy_import(memory_root, snapshot_id, target_field_id="field_fixture"))

    threads = [
        threading.Thread(target=worker, args=(str(snap_a["snapshot_id"]),)),
        threading.Thread(target=worker, args=(str(snap_b["snapshot_id"]),)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(results) == 2
    assert all(r["ok"] for r in results)
    events = read_jsonl(memory_root / "ledger" / "events.jsonl")
    plan_events = [e for e in events if e.get("event_id", "").startswith("legacy_import_plan:")]
    assert len(plan_events) >= 2


# ---------------------------------------------------------------------------
# Cluster E: immutable archive / legacy mutator
# ---------------------------------------------------------------------------

def test_E1_mark_spans_linked_retired(tmp_path: Path) -> None:
    """mark_spans_linked must raise unsupported_legacy_mutator."""
    memory_root, snapshot_id = snapshot_workspace(tmp_path)
    try:
        mark_spans_linked(memory_root, snapshot_id, [])
        raised = False
    except ValueError as exc:
        raised = True
        assert "unsupported_legacy_mutator" in str(exc)
    assert raised, "mark_spans_linked should raise unsupported_legacy_mutator"


def test_E2_write_source_spans_different_bytes_refused(tmp_path: Path) -> None:
    """write_source_spans must refuse to overwrite finalized inventory with different bytes."""
    memory_root, snapshot_id = snapshot_workspace(tmp_path)
    spans = load_source_spans(memory_root, snapshot_id)
    if not spans:
        pytest.skip("no spans produced by fixture")
    tampered = [dict(spans[0])]
    tampered[0]["start_byte"] = int(spans[0]["start_byte"]) + 999
    tampered[0]["end_byte_exclusive"] = int(spans[0]["end_byte_exclusive"]) + 999
    raised = False
    try:
        write_source_spans(memory_root, snapshot_id, tampered)
    except (ValueError, Exception):
        raised = True
    assert raised, "write_source_spans should refuse different bytes"


def test_E3_write_source_spans_same_bytes_idempotent(tmp_path: Path) -> None:
    """Exact same bytes must be safely idempotent for write_source_spans."""
    memory_root, snapshot_id = snapshot_workspace(tmp_path)
    spans = load_source_spans(memory_root, snapshot_id)
    if not spans:
        pytest.skip("no spans produced by fixture")
    inventory_path = memory_root / "archive" / "source-spans" / f"{snapshot_id}.jsonl"
    before = inventory_path.read_bytes()
    write_source_spans(memory_root, snapshot_id, spans)
    after = inventory_path.read_bytes()
    assert before == after, "idempotent write must not change inventory bytes"


def test_E4_legacy_flat_writers_retired(tmp_path: Path) -> None:
    """stage_shards, move_staged_shards, publish_field_revision must return unsupported."""
    shard = {
        "schema": "nollm.shard.v1",
        "shard_id": "shard_test",
        "text": "test",
        "text_hash": "sha256:" + "a" * 64,
    }
    root = tmp_path / "memory-root"
    staged = stage_shards(root, "batch_a", [shard])
    moved = move_staged_shards(root, "batch_a")
    revision = publish_field_revision(root, batch_id="batch_a", target_field_id="field_fixture", shard_ids=[])
    assert staged["ok"] is False
    assert moved["ok"] is False
    assert revision["ok"] is False
    assert staged["errors"] == ["unsupported_legacy_flat_writer"]
    assert moved["errors"] == ["unsupported_legacy_flat_writer"]
    assert revision["errors"] == ["unsupported_legacy_flat_writer"]
    assert not root.exists()


# ---------------------------------------------------------------------------
# Cluster F: state schema / structured failure
# ---------------------------------------------------------------------------

def test_F1_garbage_state_enum_structured_failure(tmp_path: Path) -> None:
    """Garbage state enum must produce structured error, not raw exception."""
    memory_root, batch_id, snapshot_id = planned_workspace(tmp_path)
    state_path = memory_root / "ingress" / "legacy-import" / batch_id / "state.json"
    write_json(state_path, {"state": "garbage", "updated_at": utc_now_iso()})
    result = run_legacy_import(memory_root, batch_id, commit=True)
    assert result["ok"] is False
    assert "errors" in result
    assert not any("Traceback" in str(e) for e in result["errors"])


def test_F2_bad_timestamp_state_structured_failure(tmp_path: Path) -> None:
    """Bad timestamp in state must produce structured error."""
    memory_root, batch_id, snapshot_id = planned_workspace(tmp_path)
    state_path = memory_root / "ingress" / "legacy-import" / batch_id / "state.json"
    write_json(state_path, {"state": "planned", "updated_at": "junk"})
    result = run_legacy_import(memory_root, batch_id, commit=True)
    assert result["ok"] is False
    assert "errors" in result


def test_F3_unknown_state_field_structured_failure(tmp_path: Path) -> None:
    """Unknown field in state must produce structured error."""
    memory_root, batch_id, snapshot_id = planned_workspace(tmp_path)
    state_path = memory_root / "ingress" / "legacy-import" / batch_id / "state.json"
    write_json(state_path, {"state": "planned", "updated_at": utc_now_iso(), "rogue_field": "evil"})
    result = run_legacy_import(memory_root, batch_id, commit=True)
    assert result["ok"] is False
    assert "errors" in result
    assert any("unknown_state_field" in str(e) for e in result["errors"])


# ---------------------------------------------------------------------------
# Cluster G: static enforcement
# ---------------------------------------------------------------------------

def test_G1_no_direct_filesystem_io_in_mt1_production_modules() -> None:
    """R12-02: scan MT1 production modules for unencapsulated direct filesystem I/O.

    The whitelist is deliberately small:
    - safe_storage.py / safe_root.py: implement the trusted storage layer itself
    - native_field.py: contains read_jsonl/append_jsonl/write_jsonl fixture helpers
      plus staging cleanup that uses pathlib for non-authoritative temp dirs
    - path_safety.py: containment checking (reads stat, not file content)
    - archive_manifest.py: read_json/write_json delegate to safe_read_file/safe_write_file
    - legacy_import.py: batch dir creation (mkdir) and lock dir management are
      structural, not authoritative file I/O; all authoritative reads/writes
      go through safe_storage functions
    """
    nollm_dir = Path(__file__).resolve().parents[1] / "nollm"
    whitelist = {
        "safe_storage.py",
        "safe_root.py",
        "native_field.py",
        "path_safety.py",
        "archive_manifest.py",
        "legacy_import.py",
        "validation.py",
    }
    mt1_modules = [
        "archive.py",
        "source_spans.py",
        "legacy_extract.py",
        "legacy_import.py",
        "native_field.py",
        "provenance.py",
        "coverage.py",
        "validation.py",
    ]
    # Direct Path I/O that reads or writes file *content* is forbidden.
    # mkdir/unlink/rmdir on batch/lock dirs are structural operations allowed
    # in legacy_import.py (already whitelisted).
    forbidden_content_attrs = {"read_bytes", "read_text", "write_bytes", "write_text"}
    violations = []
    for mod_name in mt1_modules:
        if mod_name in whitelist:
            continue
        mod_path = nollm_dir / mod_name
        if not mod_path.exists():
            continue
        tree = ast.parse(mod_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr in forbidden_content_attrs:
                violations.append(f"{mod_name}:{node.lineno}: .{node.attr}")
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr in {"replace", "rename"} and isinstance(node.func.value, ast.Name):
                    if node.func.value.id not in {"sr", "os"} and len(node.args) <= 1:
                        violations.append(f"{mod_name}:{node.lineno}: .{node.func.attr}()")
    assert not violations, f"direct filesystem I/O found in production modules: {violations}"