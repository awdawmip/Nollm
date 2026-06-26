from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from nollm.companion_memory_matching import rank_candidates

STORE_DIR_NAME = "native-companion-v1"
STORE_VERSION = "1"
RECORD_SCHEMA = "nollm.companion_memory_record.v1"
REMEMBER_SCHEMA = "nollm.companion_memory_remember.v1"
RECALL_SCHEMA = "nollm.companion_memory_recall.v1"
GET_SCHEMA = "nollm.companion_memory_get.v1"

ALLOWED_KINDS = {"identity", "preference", "decision", "project", "fact", "note"}
DEFAULT_KIND = "note"
ALLOWED_SCOPES = {"user", "workspace"}
DEFAULT_SCOPE = "user"
DEFAULT_SOURCE = "explicit_user"

SECRET_PATTERNS = [
    re.compile(r"Bearer\s+\S+", re.IGNORECASE),
    re.compile(r"sk-\S+", re.IGNORECASE),
    re.compile(r"ghp_\S+", re.IGNORECASE),
    re.compile(r"github_pat_\S+", re.IGNORECASE),
    re.compile(r"xox[baprs]-\S+", re.IGNORECASE),
    re.compile(r"BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY", re.IGNORECASE),
    re.compile(r"api_key\s*=\s*\S+", re.IGNORECASE),
    re.compile(r"password\s*=\s*\S+", re.IGNORECASE),
    re.compile(r"cookie\s*=\s*\S+", re.IGNORECASE),
]


class CompanionMemoryError(Exception):
    code: str
    message: str

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _normalize_text(text: str) -> str:
    return " ".join(text.strip().split())


def _canonical_key(text: str, kind: str, scope: str) -> str:
    return f"{scope}:{kind}:{_normalize_text(text)}"


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _memory_id(canonical_key: str) -> str:
    return f"nmem_{_sha256(canonical_key)[:16]}"


def _shard_id(memory_id: str) -> str:
    return f"shard_{memory_id[5:]}"


def _revision_id(memory_id: str, timestamp: str) -> str:
    return f"nrev_{timestamp.replace(':', '').replace('-', '').replace('Z', '')}_{memory_id[5:12]}"


def _content_hash(text: str) -> str:
    return _sha256(_normalize_text(text))


def _is_secret(text: str) -> bool:
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            return True
    return False


def _store_dir(out_dir: Path | str) -> Path:
    return Path(out_dir).resolve() / STORE_DIR_NAME


def _ensure_store_dir(store_dir: Path) -> None:
    store_dir.mkdir(parents=True, exist_ok=True)
    (store_dir / "revisions").mkdir(exist_ok=True)


def _manifest_path(store_dir: Path) -> Path:
    return store_dir / "manifest.json"


def _records_path(store_dir: Path) -> Path:
    return store_dir / "records.jsonl"


def _index_path(store_dir: Path) -> Path:
    return store_dir / "index.json"


def _lock_path(store_dir: Path) -> Path:
    return store_dir / ".store.lock"


@contextmanager
def _store_lock(lock_path: Path, timeout_seconds: float = 10.0) -> Iterator[None]:
    deadline = time.monotonic() + timeout_seconds
    while True:
        try:
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            try:
                os.write(fd, str(os.getpid()).encode("utf-8"))
            finally:
                os.close(fd)
            break
        except FileExistsError:
            if time.monotonic() > deadline:
                raise CompanionMemoryError("store_lock_timeout", f"Could not acquire store lock: {lock_path}")
            time.sleep(0.02)
    try:
        yield
    finally:
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass


def _read_manifest(store_dir: Path) -> dict[str, Any]:
    path = _manifest_path(store_dir)
    if not path.exists():
        now = _now_iso()
        return {
            "schema": "nollm.companion_memory_store_manifest.v1",
            "store_version": STORE_VERSION,
            "created_at": now,
            "active_revision_id": None,
        }
    return json.loads(path.read_text(encoding="utf-8"))


def _write_manifest(store_dir: Path, manifest: dict[str, Any]) -> None:
    _manifest_path(store_dir).write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


def _read_records(store_dir: Path) -> list[dict[str, Any]]:
    path = _records_path(store_dir)
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                raise CompanionMemoryError("corrupt_records", "native companion records.jsonl contains invalid JSON")
    return records


def _active_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # For W1, all appended records are active; future deletion would filter status != "active".
    return [r for r in records if r.get("status") == "active"]


def _build_index(active_records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for record in active_records:
        mid = record.get("memory_id")
        if mid:
            index[mid] = record
    return index


def _write_index(store_dir: Path, index: dict[str, dict[str, Any]]) -> None:
    tmp = _index_path(store_dir).with_suffix(".tmp")
    tmp.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(_index_path(store_dir))


def _append_record(store_dir: Path, record: dict[str, Any]) -> None:
    path = _records_path(store_dir)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _rank_records(query: str, records: list[dict[str, Any]], scope: str | None) -> tuple[list[tuple[dict[str, Any], dict[str, Any]]], dict[str, Any] | None]:
    filtered = records
    if scope is not None:
        filtered = [r for r in records if r.get("scope") == scope]
    return rank_candidates(query, filtered)


def _validate_memory_text(text: str) -> str:
    if not isinstance(text, str):
        raise CompanionMemoryError("memory_content_invalid", "memory must be a string")
    normalized = _normalize_text(text)
    if not normalized:
        raise CompanionMemoryError("memory_content_empty", "memory must not be empty or only whitespace")
    if len(normalized) > 600:
        raise CompanionMemoryError("memory_content_too_long", "memory must be 600 characters or fewer after normalization")
    if _is_secret(normalized):
        raise CompanionMemoryError("memory_content_rejected", "memory content resembles a secret or credential and is not stored")
    return normalized


def _validate_kind(kind: str | None) -> str:
    if kind is None:
        return DEFAULT_KIND
    if kind not in ALLOWED_KINDS:
        raise CompanionMemoryError("memory_kind_invalid", f"kind must be one of {sorted(ALLOWED_KINDS)}")
    return kind


def _validate_scope(scope: str | None) -> str:
    if scope is None:
        return DEFAULT_SCOPE
    if scope not in ALLOWED_SCOPES:
        raise CompanionMemoryError("memory_scope_invalid", f"scope must be one of {sorted(ALLOWED_SCOPES)}")
    return scope


def _validate_memory_id(memory_id: str) -> str:
    if not isinstance(memory_id, str) or not memory_id.startswith("nmem_"):
        raise CompanionMemoryError("native_memory_id_invalid", "memory_id must be a Nollm native id starting with nmem_")
    if re.search(r"[\\/]|\.\.|^file:|^nollm://legacy/", memory_id):
        raise CompanionMemoryError("native_memory_id_invalid", "memory_id contains illegal path or legacy locator")
    return memory_id


def remember_native_memory(
    repo_root: Path | str,
    workspace: Path | str,
    out_dir: Path | str,
    memory: str,
    kind: str | None = None,
    scope: str | None = None,
    source: str = DEFAULT_SOURCE,
) -> dict[str, Any]:
    normalized = _validate_memory_text(memory)
    kind = _validate_kind(kind)
    scope = _validate_scope(scope)

    store_dir = _store_dir(out_dir)
    _ensure_store_dir(store_dir)

    canonical = _canonical_key(normalized, kind, scope)
    memory_id = _memory_id(canonical)
    shard_id = _shard_id(memory_id)
    content_hash = _content_hash(normalized)
    timestamp = _now_iso()
    revision_id = _revision_id(memory_id, timestamp)

    with _store_lock(_lock_path(store_dir)):
        manifest = _read_manifest(store_dir)
        active_records = _active_records(_read_records(store_dir))
        index = _build_index(active_records)

        existing = index.get(memory_id)
        if existing is not None and existing.get("content_hash") == content_hash:
            return {
                "schema": REMEMBER_SCHEMA,
                "ok": True,
                "created": False,
                "deduplicated": True,
                "memory_id": existing["memory_id"],
                "shard_id": existing["shard_id"],
                "revision_id": existing["revision_id"],
                "text_excerpt": existing["text"],
                "source": existing["source"],
                "store": "nollm_native_companion",
            }

        record = {
            "schema": RECORD_SCHEMA,
            "memory_id": memory_id,
            "shard_id": shard_id,
            "revision_id": revision_id,
            "text": normalized,
            "kind": kind,
            "scope": scope,
            "source": source,
            "created_at": timestamp,
            "content_hash": content_hash,
            "status": "active",
        }
        _append_record(store_dir, record)
        new_index = _build_index(_active_records(_read_records(store_dir)))
        _write_index(store_dir, new_index)
        manifest["active_revision_id"] = revision_id
        _write_manifest(store_dir, manifest)

    return {
        "schema": REMEMBER_SCHEMA,
        "ok": True,
        "created": True,
        "deduplicated": False,
        "memory_id": memory_id,
        "shard_id": shard_id,
        "revision_id": revision_id,
        "text_excerpt": normalized,
        "source": source,
        "store": "nollm_native_companion",
    }


def recall_native_memory(
    repo_root: Path | str,
    workspace: Path | str,
    out_dir: Path | str,
    query: str,
    limit: int = 5,
    scope: str | None = None,
) -> dict[str, Any]:
    if not isinstance(query, str) or not _normalize_text(query):
        raise CompanionMemoryError("recall_query_empty", "query must be a non-empty string")
    if limit < 1:
        limit = 1

    store_dir = _store_dir(out_dir)
    if not store_dir.exists():
        return {
            "schema": RECALL_SCHEMA,
            "ok": True,
            "query": query,
            "results": [],
            "warnings": ["native companion store does not exist yet"],
            "store": "nollm_native_companion",
        }

    with _store_lock(_lock_path(store_dir)):
        active_records = _active_records(_read_records(store_dir))

    ranked, ambiguity = _rank_records(query, active_records, scope)
    selected = ranked[:limit]

    if ambiguity is not None:
        return {
            "schema": RECALL_SCHEMA,
            "ok": True,
            "query": query,
            "results": [],
            "warnings": [
                "multiple native companion memories match a generic query; ask for a more specific memory facet"
            ],
            "explicit_absences": [
                "No uniquely relevant Nollm native companion memory could be selected."
            ],
            "ambiguity": ambiguity,
            "store": "nollm_native_companion",
        }

    if not selected:
        return {
            "schema": RECALL_SCHEMA,
            "ok": True,
            "query": query,
            "results": [],
            "warnings": ["no relevant native companion memory found"],
            "explicit_absences": ["No Nollm native companion memory matched this query."],
            "store": "nollm_native_companion",
        }

    results = []
    for r, match in selected:
        results.append(
            {
                "memory_id": r["memory_id"],
                "shard_id": r["shard_id"],
                "text": r["text"],
                "kind": r["kind"],
                "scope": r["scope"],
                "source": r["source"],
                "revision_id": r["revision_id"],
                "match": {
                    "mode": match["mode"],
                    "matched_terms": match["matched_terms"],
                    "matched_facets": match["matched_facets"],
                },
            }
        )

    return {
        "schema": RECALL_SCHEMA,
        "ok": True,
        "query": query,
        "results": results,
        "warnings": [],
        "store": "nollm_native_companion",
    }


def get_native_memory(
    repo_root: Path | str,
    workspace: Path | str,
    out_dir: Path | str,
    memory_id: str,
) -> dict[str, Any]:
    memory_id = _validate_memory_id(memory_id)
    store_dir = _store_dir(out_dir)
    if not store_dir.exists():
        return {
            "schema": GET_SCHEMA,
            "ok": False,
            "status": "not_found",
            "memory_id": memory_id,
            "error": {
                "code": "native_memory_not_found",
                "message": "native companion store does not exist",
                "retryable": False,
            },
            "store": "nollm_native_companion",
        }

    with _store_lock(_lock_path(store_dir)):
        active_records = _active_records(_read_records(store_dir))
        index = _build_index(active_records)
        record = index.get(memory_id)

    if record is None:
        return {
            "schema": GET_SCHEMA,
            "ok": False,
            "status": "not_found",
            "memory_id": memory_id,
            "error": {
                "code": "native_memory_not_found",
                "message": "native memory not found",
                "retryable": False,
            },
            "store": "nollm_native_companion",
        }

    return {
        "schema": GET_SCHEMA,
        "ok": True,
        "status": "found",
        "memory_id": memory_id,
        "record": {
            "memory_id": record["memory_id"],
            "shard_id": record["shard_id"],
            "text": record["text"],
            "kind": record["kind"],
            "scope": record["scope"],
            "source": record["source"],
            "revision_id": record["revision_id"],
            "created_at": record["created_at"],
            "content_hash": record["content_hash"],
            "status": record["status"],
        },
        "store": "nollm_native_companion",
    }


def native_store_summary(out_dir: Path | str) -> dict[str, Any]:
    store_dir = _store_dir(out_dir)
    if not store_dir.exists():
        return {"record_count": 0, "active_revision_id": None, "store_available": False}
    try:
        with _store_lock(_lock_path(store_dir)):
            manifest = _read_manifest(store_dir)
            active_records = _active_records(_read_records(store_dir))
        return {
            "record_count": len(active_records),
            "active_revision_id": manifest.get("active_revision_id"),
            "store_available": True,
        }
    except Exception:
        return {"record_count": 0, "active_revision_id": None, "store_available": False}
