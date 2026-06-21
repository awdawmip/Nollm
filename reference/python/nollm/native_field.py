from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .archive import memory_root_path, utc_now
from .archive_manifest import canonical_json, read_json, sha256_bytes, write_json


FIELD_REVISION_SCHEMA = "nollm.native_field_revision.v1"
SHARD_SCHEMA = "nollm.native_dream_shard.v1"


def shard_id_for(idempotence_key: str) -> str:
    return "shard_" + idempotence_key.removeprefix("sha256:")[:24]


def build_shard(record: dict[str, Any], *, batch_id: str, source_policy_id: str, idempotence_key: str) -> dict[str, Any]:
    return {
        "schema": SHARD_SCHEMA,
        "shard_id": shard_id_for(idempotence_key),
        "batch_id": batch_id,
        "origin_kind": record.get("origin_kind", "legacy_import"),
        "operational_state": record.get("operational_state", "loose"),
        "epistemic_state": record.get("epistemic_state", "legacy_recorded"),
        "source_policy_id": source_policy_id,
        "source_refs": [record["source_ref"]],
        "continuity_refs": [record["span_id"]],
        "geometry_intent": {
            "mode": "archive_ingest_seed",
            "placement": "pending_cortex_orientation",
        },
        "anchor_field_weights": {},
        "text": record["text"],
        "text_hash": record["text_hash"],
        "idempotence_key": idempotence_key,
        "created_at": utc_now(),
    }


def existing_shards_by_key(memory_root: Path | str) -> dict[str, dict[str, Any]]:
    root = memory_root_path(memory_root)
    shards: dict[str, dict[str, Any]] = {}
    active_ids = set(_current_head_shards(root))
    if not active_ids:
        return shards
    for path in sorted((root / "field" / "shards").glob("*.json")):
        data = read_json(path)
        if active_ids and data.get("shard_id") not in active_ids:
            continue
        key = data.get("idempotence_key")
        if isinstance(key, str):
            shards[key] = data
    return shards


def stage_shards(memory_root: Path | str, batch_id: str, shards: list[dict[str, Any]]) -> Path:
    root = memory_root_path(memory_root)
    staging = root / "field" / ".staging" / batch_id
    if staging.exists():
        for path in sorted(staging.glob("*.json")):
            path.unlink()
    staging.mkdir(parents=True, exist_ok=True)
    for shard in shards:
        write_json(staging / f"{shard['shard_id']}.json", shard)
    return staging


def publish_field_revision(memory_root: Path | str, *, batch_id: str, target_field_id: str, shard_ids: list[str]) -> dict[str, Any]:
    root = memory_root_path(memory_root)
    existing_ids = _current_field_shards(root, target_field_id)
    merged_ids = sorted(set(existing_ids).union(shard_ids))
    revision_seed = canonical_json({"batch_id": batch_id, "field_id": target_field_id, "shard_ids": merged_ids})
    revision_id = "fieldrev_" + sha256_bytes(revision_seed)[:20]
    revision = {
        "schema": FIELD_REVISION_SCHEMA,
        "field_revision_id": revision_id,
        "field_id": target_field_id,
        "batch_id": batch_id,
        "created_at": utc_now(),
        "shard_ids": merged_ids,
        "shard_count": len(merged_ids),
    }
    write_json(root / "field" / "revisions" / f"{revision_id}.json", revision)
    write_json(root / "field" / "HEAD.json", {"field_id": target_field_id, "field_revision_id": revision_id})
    return revision


def move_staged_shards(memory_root: Path | str, batch_id: str) -> list[str]:
    root = memory_root_path(memory_root)
    staging = root / "field" / ".staging" / batch_id
    target = root / "field" / "shards"
    target.mkdir(parents=True, exist_ok=True)
    moved: list[str] = []
    for path in sorted(staging.glob("*.json")):
        data = read_json(path)
        out = target / path.name
        if not out.exists():
            out.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        moved.append(str(data["shard_id"]))
    return moved


def load_field_head(memory_root: Path | str) -> dict[str, Any] | None:
    path = memory_root_path(memory_root) / "field" / "HEAD.json"
    if not path.exists():
        return None
    return read_json(path)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records), encoding="utf-8")


def _current_field_shards(root: Path, target_field_id: str) -> list[str]:
    head = root / "field" / "HEAD.json"
    if not head.exists():
        return []
    current = read_json(head)
    if current.get("field_id") != target_field_id:
        return []
    revision_path = root / "field" / "revisions" / f"{current['field_revision_id']}.json"
    if not revision_path.exists():
        return []
    return [str(item) for item in read_json(revision_path).get("shard_ids", [])]


def _current_head_shards(root: Path) -> list[str]:
    head = root / "field" / "HEAD.json"
    if not head.exists():
        return []
    current = read_json(head)
    revision_path = root / "field" / "revisions" / f"{current['field_revision_id']}.json"
    if not revision_path.exists():
        return []
    return [str(item) for item in read_json(revision_path).get("shard_ids", [])]
