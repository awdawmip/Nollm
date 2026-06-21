from __future__ import annotations

import json
from pathlib import Path

from nollm.archive import create_archive_snapshot
from nollm.archive_manifest import read_json, write_json
from nollm.legacy_extract import extract_legacy_spans, idempotence_key
from nollm.legacy_import import plan_legacy_import, run_legacy_import, validate_legacy_import
from nollm.legacy_text import NORMALIZATION_ID, normalize_legacy_text, text_hash
from nollm.source_spans import build_source_span_inventory


def test_t1_t2_t3_shard_text_and_hash_fields_are_bound_to_archive(tmp_path: Path) -> None:
    memory_root, batch_id, revision_id = commit_workspace(tmp_path, {"MEMORY.md": "# M\n\nArchived source text\n"})
    shard_path = next((memory_root / "field" / "publications" / revision_id / "shards").glob("*.json"))

    shard = read_json(shard_path)
    shard["text"] = "TAMPERED CONTENT THAT IS NOT THE ARCHIVED SOURCE"
    write_json(shard_path, shard)
    assert validate_legacy_import(memory_root, batch_id)["ok"] is False

    memory_root, batch_id, revision_id = commit_workspace(tmp_path / "raw", {"MEMORY.md": "# M\n\nArchived source text\n"})
    shard_path = next((memory_root / "field" / "publications" / revision_id / "shards").glob("*.json"))
    shard = read_json(shard_path)
    shard["source_range_hash"] = "sha256:" + "0" * 64
    write_json(shard_path, shard)
    assert validate_legacy_import(memory_root, batch_id)["ok"] is False

    memory_root, batch_id, revision_id = commit_workspace(tmp_path / "norm", {"MEMORY.md": "# M\n\nArchived source text\n"})
    shard_path = next((memory_root / "field" / "publications" / revision_id / "shards").glob("*.json"))
    shard = read_json(shard_path)
    shard["text_hash"] = "sha256:" + "1" * 64
    write_json(shard_path, shard)
    assert validate_legacy_import(memory_root, batch_id)["ok"] is False
    shard["text_hash"] = text_hash(shard["text"])
    shard["normalization_id"] = "wrong"
    write_json(shard_path, shard)
    assert validate_legacy_import(memory_root, batch_id)["ok"] is False


def test_t4_normalization_is_shared_by_extractor_idempotence_and_validator(tmp_path: Path) -> None:
    text = "# M\r\n\r\nAlpha\t beta\r\n gamma\n"
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True)
    (workspace / "MEMORY.md").write_text(text, encoding="utf-8", newline="")
    memory_root = tmp_path / "memory-root"
    snapshot_id = str(create_archive_snapshot(workspace, memory_root)["snapshot_id"])
    build_source_span_inventory(memory_root, snapshot_id)
    records = extract_legacy_spans(memory_root, snapshot_id)

    assert records[0]["text"] == "Alpha beta gamma"
    assert records[0]["normalization_id"] == NORMALIZATION_ID
    assert idempotence_key(records[0], "openclaw_legacy_v1") == idempotence_key({**records[0], "text": "Alpha   beta\n gamma"}, "openclaw_legacy_v1")
    plan = plan_legacy_import(memory_root, snapshot_id, target_field_id="field_fixture")
    commit = run_legacy_import(memory_root, str(plan["batch_id"]), commit=True)
    assert commit["ok"] is True
    assert validate_legacy_import(memory_root, str(plan["batch_id"]))["ok"] is True


def commit_workspace(tmp_path: Path, files: dict[str, str]) -> tuple[Path, str, str]:
    workspace = tmp_path / "workspace"
    for relative, content in files.items():
        path = workspace / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    memory_root = tmp_path / "memory-root"
    snapshot_id = str(create_archive_snapshot(workspace, memory_root)["snapshot_id"])
    plan = plan_legacy_import(memory_root, snapshot_id, target_field_id="field_fixture")
    commit = run_legacy_import(memory_root, str(plan["batch_id"]), commit=True)
    assert commit["ok"] is True
    return memory_root, str(plan["batch_id"]), str(commit["field_revision_id"])
