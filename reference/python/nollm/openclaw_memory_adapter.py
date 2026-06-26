from __future__ import annotations

import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from nollm.dream_shard import DreamShard, shard_to_record, is_independently_meaningful
from nollm.geometry_profiles import default_geometry_profile
from nollm.gravity import (
    GravityMark,
    gravity_mark_to_record,
)

from nollm.companion_memory_store import (
    CompanionMemoryError,
    get_native_memory as _store_get_native_memory,
    native_store_summary,
    recall_native_memory as _store_recall_native_memory,
    remember_native_memory as _store_remember_native_memory,
)

REMEMBER_NATIVE_SCHEMA = "nollm.companion_memory_remember.v1"
RECALL_NATIVE_SCHEMA = "nollm.companion_memory_recall.v1"
GET_NATIVE_SCHEMA = "nollm.companion_memory_get.v1"

SCHEMA = "nollm.openclaw_memory_fixture_index.v1"
SIDECAR_SCHEMA = "nollm.openclaw_memory_sidecar.v1"
SEARCH_SCHEMA = "nollm.openclaw_memory_sidecar_search.v1"
GET_SCHEMA = "nollm.openclaw_memory_sidecar_get.v1"
STATUS_SCHEMA = "nollm.openclaw_memory_sidecar_status.v1"
WRITE_SCHEMA = "nollm.openclaw_memory_sidecar_write_candidate.v1"
COMMIT_SCHEMA = "nollm.openclaw_memory_sidecar_commit_candidate.v1"
RECALL_SCHEMA = "nollm.openclaw_memory_sidecar_recall.v1"
DEFAULT_PROFILE = "default_dream"

DEFAULT_CHART = "openclaw_memory_fixture"
STATUS = "experimental_internal_sidecar"
LAYOUT_METHOD = "semantic_local_v1"
FORBIDDEN_SEMANTICS = {
    "real_openclaw_plugin": False,
    "real_llm_call": False,
    "memory_slot_replacement": False,
    "auto_memory_write": False,
    "drift_class_trust_mapping": False,
    "hard_drift_rejection": False,
    "stable_public_recall_api": False,
}


@dataclass(frozen=True)
class OpenClawMemoryChunk:
    memory_id: str
    source_path: str
    line_range: tuple[int, int]
    text: str
    source_role: str
    heading_path: tuple[str, ...]
    source_sha256: str
    chunk_sha256: str

    @property
    def candidate_id(self) -> str:
        return self.memory_id.replace("mem_", "cand_", 1)

    @property
    def source_kind(self) -> str:
        return _source_kind_from_role(self.source_role)

    @property
    def date(self) -> str | None:
        match = re.fullmatch(r"memory/(\d{4}-\d{2}-\d{2})\.md", self.source_path)
        return match.group(1) if match else None

    def to_record(self) -> dict[str, object]:
        record: dict[str, object] = {
            "memory_id": self.memory_id,
            "candidate_id": self.candidate_id,
            "source_path": self.source_path,
            "source_kind": self.source_kind,
            "source_role": self.source_role,
            "line_start": self.line_range[0],
            "line_end": self.line_range[1],
            "line_range": list(self.line_range),
            "text": self.text,
            "heading_path": list(self.heading_path),
            "provenance": _provenance(self.source_path, self.line_range),
            "version_status": "fixture_current",
            "trust_level": "unverified_fixture",
            "source_sha256": self.source_sha256,
            "chunk_sha256": self.chunk_sha256,
        }
        if self.date is not None:
            record["date"] = self.date
        return record


@dataclass(frozen=True)
class OpenClawMemoryIndex:
    workspace_root: str
    chunk_count: int
    chunks: tuple[OpenClawMemoryChunk, ...]
    warnings: tuple[str, ...]
    source_files: tuple[str, ...]

    def to_record(self) -> dict[str, object]:
        return {
            "workspace_root": self.workspace_root,
            "chunk_count": self.chunk_count,
            "source_files": list(self.source_files),
            "chunks": [chunk.to_record() for chunk in self.chunks],
            "warnings": list(self.warnings),
        }


def parse_openclaw_memory_workspace(workspace_root: Path | str) -> OpenClawMemoryIndex:
    root = Path(workspace_root).resolve()
    warnings: list[str] = []
    chunks: list[OpenClawMemoryChunk] = []
    source_files: list[str] = []

    if not root.exists():
        warnings.append("workspace_missing")
        return OpenClawMemoryIndex(str(root), 0, (), tuple(warnings), ())

    for path in _memory_source_files(root):
        relative = _relative_posix(root, path)
        source_files.append(relative)
        chunks.extend(_parse_markdown_file(path, source_path=relative, source_role=_source_role(relative)))

    return OpenClawMemoryIndex(
        workspace_root=str(root),
        chunk_count=len(chunks),
        chunks=tuple(chunks),
        warnings=tuple(warnings),
        source_files=tuple(source_files),
    )


def build_sidecar_store(repo_root: Path | str, workspace: Path | str, out_dir: Path | str) -> dict[str, object]:
    repo = Path(repo_root).resolve()
    workspace_path = Path(workspace).resolve()
    out = Path(out_dir).resolve()
    index = parse_openclaw_memory_workspace(workspace_path)
    candidates = [chunk.to_record() for chunk in index.chunks]
    shards = [_shard_record(chunk) for chunk in index.chunks]
    shards = [shard for shard in shards if shard is not None]
    marks = [_geometry_mark_record(chunk) for chunk in index.chunks]
    manifest = _sidecar_manifest(repo, workspace_path, out, index, candidates, shards, marks)
    sidecar_report = {
        "schema": SIDECAR_SCHEMA,
        "ok": not any(FORBIDDEN_SEMANTICS.values()),
        "status": STATUS,
        "workspace": _display_path(repo, workspace_path),
        "out_dir": _display_path(repo, out),
        "source_files": list(index.source_files),
        "source_roles_present": _source_roles_present(candidates),
        "accepted_get_id_forms": ["candidate_id", "memory_id", "shard_id"],
        "durable_memory_mutation": False,
        "candidate_count": len(candidates),
        "shard_count": len(shards),
        "geometry_mark_count": len(marks),
        "forbidden_semantics": dict(FORBIDDEN_SEMANTICS),
        "warnings": list(index.warnings),
    }

    out.mkdir(parents=True, exist_ok=True)
    _write_jsonl(out / "candidates.jsonl", candidates)
    _write_jsonl(out / "shards.jsonl", shards)
    _write_jsonl(out / "geometry_marks.jsonl", marks)
    if not (out / "pending_writes.jsonl").exists():
        _write_jsonl(out / "pending_writes.jsonl", [])
    if not (out / "commit_ledger.jsonl").exists():
        _write_jsonl(out / "commit_ledger.jsonl", [])
    _write_json(out / "sidecar_manifest.json", manifest)
    _write_json(out / "openclaw_memory_sidecar_report.json", sidecar_report)
    return sidecar_report


def search_sidecar(
    repo_root: Path | str,
    workspace: Path | str,
    out_dir: Path | str,
    *,
    query: str,
    limit: int = 5,
) -> dict[str, object]:
    if not query.strip():
        raise ValueError("query must be non-empty")
    if limit < 1:
        raise ValueError("limit must be positive")
    build_sidecar_store(repo_root, workspace, out_dir)
    out = Path(out_dir).resolve()
    candidates = _read_jsonl(out / "candidates.jsonl")
    marks = {str(item["content_id"]): item for item in _read_jsonl(out / "geometry_marks.jsonl")}
    shards = {str(item["candidate_id"]): item for item in _read_jsonl(out / "shards.jsonl")}
    scored: list[dict[str, object]] = []
    for candidate in candidates:
        candidate_id = str(candidate["candidate_id"])
        if candidate_id not in shards:
            continue
        scored.append(
            {
                "candidate": candidate,
                "retrieval_score": _lexical_score(query, str(candidate["text"])),
                "geometry_mark": marks[candidate_id],
                "shard": shards[candidate_id],
            }
        )
    scored.sort(
        key=lambda item: (
            -float(item["retrieval_score"]),
            str(item["candidate"]["source_path"]),
            int(item["candidate"]["line_start"]),
            str(item["candidate"]["candidate_id"]),
        )
    )
    well = _query_well(query, scored)
    for item in scored:
        item["gravity_report"] = _gravity_report(query, well, item)
    results = [_search_result_record(item) for item in scored[:limit]]
    report = {
        "schema": SEARCH_SCHEMA,
        "ok": True,
        "status": STATUS,
        "query": query,
        "limit": limit,
        "gravity_well": well,
        "result_count": len(results),
        "results": results,
        "forbidden_semantics": dict(FORBIDDEN_SEMANTICS),
        "warnings": ["drift_class is instrumentation, not trust/status or a hard filter"],
    }
    _write_json(out / "last_search_report.json", report)
    return report


def get_sidecar_item(repo_root: Path | str, workspace: Path | str, out_dir: Path | str, item_id: str) -> dict[str, object]:
    if not item_id:
        raise ValueError("id must be non-empty")
    build_sidecar_store(repo_root, workspace, out_dir)
    out = Path(out_dir).resolve()
    candidates = _read_jsonl(out / "candidates.jsonl")
    shards = _read_jsonl(out / "shards.jsonl")
    marks = {str(item["content_id"]): item for item in _read_jsonl(out / "geometry_marks.jsonl")}
    candidate = _find_candidate(candidates, shards, item_id)
    if candidate is None:
        return {
            "schema": GET_SCHEMA,
            "ok": False,
            "status": STATUS,
            "id": item_id,
            "error": "not_found",
            "forbidden_semantics": dict(FORBIDDEN_SEMANTICS),
        }
    cached_search = _last_search_item(out, str(candidate["candidate_id"]))
    report = {
        "schema": GET_SCHEMA,
        "ok": True,
        "status": STATUS,
        "id": item_id,
        "candidate": candidate,
        "source_metadata": {
            "source_path": candidate["source_path"],
            "line_start": candidate["line_start"],
            "line_end": candidate["line_end"],
            "heading_path": candidate["heading_path"],
            "provenance": candidate["provenance"],
        },
        "text": candidate["text"],
        "geometry_mark": marks[str(candidate["candidate_id"])],
        "gravity_report": cached_search.get("gravity_report") if cached_search else None,
        "provenance": candidate["provenance"],
        "forbidden_semantics": dict(FORBIDDEN_SEMANTICS),
    }
    _write_json(out / "last_get_report.json", report)
    return report


def write_candidate(
    repo_root: Path | str,
    workspace: Path | str,
    out_dir: Path | str,
    *,
    text: str,
    source: str,
    why: str = "pending explicit review before durable promotion",
) -> dict[str, object]:
    return {
        "schema": WRITE_SCHEMA,
        "ok": False,
        "status": STATUS,
        "error": "source_memory_write_disabled",
        "message": "Nollm does not write or stage writes for OpenClaw source memory files in OCP6S.",
        "durable_write": False,
        "target_files_mutated": False,
        "durable_memory_mutation": False,
        "forbidden_semantics": dict(FORBIDDEN_SEMANTICS),
    }


def commit_candidate(
    repo_root: Path | str,
    workspace: Path | str,
    out_dir: Path | str,
    *,
    candidate_id: str,
    explicit_confirmation: bool,
    target: str,
    reason: str,
    source: str,
) -> dict[str, object]:
    return {
        "schema": COMMIT_SCHEMA,
        "ok": False,
        "status": STATUS,
        "candidate_id": candidate_id,
        "error": "source_memory_write_disabled",
        "message": "Nollm does not commit to OpenClaw source memory files in OCP6S.",
        "durable_write": False,
        "target_files_mutated": False,
        "memory_core_reindex_required": False,
        "forbidden_semantics": dict(FORBIDDEN_SEMANTICS),
    }


def recall_sidecar(
    repo_root: Path | str,
    workspace: Path | str,
    out_dir: Path | str,
    *,
    query: str,
    limit: int = 6,
) -> dict[str, object]:
    search = search_sidecar(repo_root, workspace, out_dir, query=query, limit=limit)
    direct: list[dict[str, object]] = []
    lateral: list[dict[str, object]] = []
    cautions: list[str] = []
    for result in search["results"]:  # type: ignore[index]
        if not isinstance(result, Mapping):
            continue
        score = float(result.get("retrieval_score") or 0.0)
        if score <= 0.0:
            continue
        record = _recall_item(result)
        role = str(result.get("source_role") or "")
        drift = str((result.get("gravity_report") or {}).get("drift_class")) if isinstance(result.get("gravity_report"), Mapping) else ""
        if role == "dreams" or drift in {"far_weak", "semantic_break", "unglued", "chart_jump"}:
            lateral.append(record)
            if role == "dreams":
                cautions.append("DREAMS source is speculative/lateral and must not override durable evidence.")
            if drift == "semantic_break":
                cautions.append("semantic_break is a caution, not a rejection rule.")
        else:
            direct.append(record)
    if not direct and not lateral:
        cautions.append("No relevant Nollm local memory evidence found.")
    report = {
        "schema": RECALL_SCHEMA,
        "ok": True,
        "status": STATUS,
        "candidate_source": "nollm_local",
        "query": query,
        "direct_evidence": direct,
        "lateral_context": lateral,
        "cautions": sorted(set(cautions)),
        "return_vector": None,
        "use_instruction": (
            "Use direct evidence for factual claims; inspect cited sources before relying on lateral context. "
            "Treat drift labels as orientation only."
        ),
        "forbidden_semantics": dict(FORBIDDEN_SEMANTICS),
    }
    _write_json(Path(out_dir).resolve() / "last_recall_report.json", report)
    return report


def remember_native_companion_memory(
    repo_root: Path | str,
    workspace: Path | str,
    out_dir: Path | str,
    *,
    memory: str,
    kind: str | None = None,
    scope: str | None = None,
    source: str = "explicit_user",
) -> dict[str, object]:
    try:
        return _store_remember_native_memory(
            repo_root, workspace, out_dir, memory=memory, kind=kind, scope=scope, source=source
        )
    except CompanionMemoryError as exc:
        return {
            "schema": REMEMBER_NATIVE_SCHEMA,
            "ok": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "retryable": False,
            },
            "store": "nollm_native_companion",
        }


def recall_native_companion_memory(
    repo_root: Path | str,
    workspace: Path | str,
    out_dir: Path | str,
    *,
    query: str,
    limit: int = 5,
    scope: str | None = None,
) -> dict[str, object]:
    try:
        return _store_recall_native_memory(
            repo_root, workspace, out_dir, query=query, limit=limit, scope=scope
        )
    except CompanionMemoryError as exc:
        return {
            "schema": RECALL_NATIVE_SCHEMA,
            "ok": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "retryable": False,
            },
            "store": "nollm_native_companion",
        }


def get_native_companion_memory(
    repo_root: Path | str,
    workspace: Path | str,
    out_dir: Path | str,
    memory_id: str,
) -> dict[str, object]:
    try:
        return _store_get_native_memory(repo_root, workspace, out_dir, memory_id)
    except CompanionMemoryError as exc:
        return {
            "schema": GET_NATIVE_SCHEMA,
            "ok": False,
            "status": "not_found",
            "memory_id": memory_id,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "retryable": False,
            },
            "store": "nollm_native_companion",
        }


def sidecar_status(repo_root: Path | str, workspace: Path | str, out_dir: Path | str) -> dict[str, object]:
    repo = Path(repo_root).resolve()
    out = Path(out_dir).resolve()
    workspace_path = Path(workspace).resolve()
    current_path = out / "current_field.json"
    manifest_path = out / "sidecar_manifest.json"
    manifest = _read_json(manifest_path) if manifest_path.exists() else {}
    current_field = None
    current_pointer = _read_json(current_path) if current_path.exists() else None
    if isinstance(current_pointer, Mapping):
        field_path = out / str(current_pointer.get("path", "")) / "dream_field.json"
        if field_path.exists():
            current_field = _read_json(field_path)
    snapshot_hash = _source_snapshot_hash_for_status(workspace_path)
    field_hash = str(current_field.get("source_snapshot_hash")) if isinstance(current_field, Mapping) else None
    dreamer_ref = current_field.get("dreamer_run_ref") if isinstance(current_field, Mapping) else None
    report = {
        "schema": STATUS_SCHEMA,
        "ok": True,
        "status": STATUS,
        "python_executable": Path(sys.executable).resolve().as_posix(),
        "python_version": sys.version.split()[0],
        "python_prefix": Path(sys.prefix).resolve().as_posix(),
        "platform": sys.platform,
        "workspace": _display_path(repo, workspace_path),
        "out_dir": _display_path(repo, out),
        "manifest": manifest,
        "field_available": current_field is not None,
        "field_id": current_field.get("field_id") if isinstance(current_field, Mapping) else None,
        "current_revision_id": current_field.get("revision_id") if isinstance(current_field, Mapping) else None,
        "field_stale": bool(field_hash and snapshot_hash and field_hash != snapshot_hash),
        "source_snapshot_hash": field_hash,
        "current_source_snapshot_hash": snapshot_hash,
        "dreamer_last_status": _dreamer_last_status(dreamer_ref),
        "durable_memory_mutation": False,
        "accepted_get_id_forms": ["candidate_id", "memory_id", "shard_id"],
        "source_roles_present": manifest.get("source_roles_present", []),
        "counts": {
            "candidates": len(_read_jsonl(out / "candidates.jsonl")) if (out / "candidates.jsonl").exists() else 0,
            "shards": len(_read_jsonl(out / "shards.jsonl")) if (out / "shards.jsonl").exists() else 0,
            "geometry_marks": len(_read_jsonl(out / "geometry_marks.jsonl")) if (out / "geometry_marks.jsonl").exists() else 0,
            "pending_writes": len(_read_jsonl(out / "pending_writes.jsonl")) if (out / "pending_writes.jsonl").exists() else 0,
            "commit_ledger": len(_read_jsonl(out / "commit_ledger.jsonl")) if (out / "commit_ledger.jsonl").exists() else 0,
        },
        "legacy_search_tools_registered": False,
        "forbidden_semantics": dict(FORBIDDEN_SEMANTICS),
    }
    report["native_companion_memory"] = native_store_summary(out_dir)
    _write_json(out / "last_status_report.json", report)
    return report


def build_openclaw_memory_fixture_report(repo_root: Path | str, workspace: Path | str) -> dict[str, object]:
    repo = Path(repo_root).resolve()
    workspace_path = Path(workspace).resolve()
    index = parse_openclaw_memory_workspace(workspace_path)
    record = index.to_record()
    report = {
        "schema": SCHEMA,
        "ok": not any(FORBIDDEN_SEMANTICS.values()),
        "workspace": _display_path(repo, workspace_path),
        "chunk_count": record["chunk_count"],
        "source_files": record["source_files"],
        "source_roles_present": _source_roles_present(record["chunks"]),  # type: ignore[arg-type]
        "chunks": record["chunks"],
        "warnings": record["warnings"],
        "forbidden_semantics": dict(FORBIDDEN_SEMANTICS),
    }
    _assert_json_primitive(report)
    return report


def write_openclaw_memory_fixture_report(report: Mapping[str, object], output: Path | str) -> None:
    _write_json(Path(output), report)


def _memory_source_files(root: Path) -> list[Path]:
    files: list[Path] = []
    memory = root / "MEMORY.md"
    dreams = root / "DREAMS.md"
    if memory.exists():
        files.append(memory)
    memory_dir = root / "memory"
    if memory_dir.exists():
        files.extend(sorted(path for path in memory_dir.glob("*.md") if path.is_file()))
    if dreams.exists():
        files.append(dreams)
    return files


def _source_snapshot_hash_for_status(root: Path) -> str:
    stable = []
    for path in _memory_source_files(root):
        data = path.read_bytes()
        stable.append(
            {
                "source_path": path.relative_to(root).as_posix(),
                "sha256": _sha256_bytes(data),
                "byte_count": len(data),
                "line_count": len(data.decode("utf-8", errors="replace").splitlines()),
            }
        )
    stable.sort(key=lambda item: str(item["source_path"]))
    return _sha256_text(json.dumps(stable, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def _dreamer_last_status(dreamer_ref: object) -> str:
    if not isinstance(dreamer_ref, Mapping):
        return "blocked"
    kind = str(dreamer_ref.get("kind", ""))
    if kind == "live_openclaw_agent":
        return "published"
    if kind in {"mock_openclaw_dreamer", "explicit_fixture", "mock_or_operator_supplied"}:
        return "published"
    return "blocked"


def _parse_markdown_file(path: Path, *, source_path: str, source_role: str) -> list[OpenClawMemoryChunk]:
    data = path.read_bytes()
    source_sha256 = _sha256_bytes(data)
    lines = data.decode("utf-8", errors="replace").splitlines()
    chunks: list[OpenClawMemoryChunk] = []
    headings: list[str] = []
    block: list[tuple[int, str]] = []

    def flush_block() -> None:
        if not block:
            return
        text = "\n".join(line.strip() for _, line in block).strip()
        start = block[0][0]
        end = block[-1][0]
        block.clear()
        if not text:
            return
        chunk_sha256 = _sha256_text(text)
        memory_id = _memory_id(source_path, (start, end), chunk_sha256)
        chunks.append(
            OpenClawMemoryChunk(
                memory_id=memory_id,
                source_path=source_path,
                line_range=(start, end),
                text=text,
                source_role=source_role,
                heading_path=tuple(headings),
                source_sha256=source_sha256,
                chunk_sha256=chunk_sha256,
            )
        )

    for line_number, line in enumerate(lines, start=1):
        heading = _parse_heading(line)
        if heading is not None:
            flush_block()
            level, title = heading
            headings = headings[: max(0, level - 1)]
            headings.append(title)
            continue
        if line.strip() == "":
            flush_block()
            continue
        block.append((line_number, line))
    flush_block()
    return chunks


def _parse_heading(line: str) -> tuple[int, str] | None:
    stripped = line.strip()
    if not stripped.startswith("#"):
        return None
    marks = len(stripped) - len(stripped.lstrip("#"))
    if marks == 0 or marks > 6:
        return None
    if len(stripped) <= marks or stripped[marks] != " ":
        return None
    title = stripped[marks:].strip()
    if not title:
        return None
    return marks, title


def _source_role(source_path: str) -> str:
    if source_path == "MEMORY.md":
        return "durable_memory"
    if source_path == "DREAMS.md":
        return "dreams"
    if source_path.startswith("memory/") and source_path.endswith(".md"):
        return "daily_memory"
    return "unknown"


def _source_kind_from_role(source_role: str) -> str:
    return {
        "durable_memory": "long_term",
        "daily_memory": "daily",
        "dreams": "dream",
    }.get(source_role, "unknown")


def _shard_record(chunk: OpenClawMemoryChunk) -> dict[str, object]:
    shard_id = _shard_id(chunk.candidate_id, chunk.chunk_sha256)
    anchor = _anchor_vector(chunk.text)
    if not is_independently_meaningful(chunk.text):
        return None
    shard = DreamShard(
        shard_id=shard_id,
        text=chunk.text,
        source="imported_text",
        status="candidate",
        anchors_hint=tuple(anchor.keys()),
        metadata={
            "candidate_id": chunk.candidate_id,
            "source_path": chunk.source_path,
            "line_start": str(chunk.line_range[0]),
            "line_end": str(chunk.line_range[1]),
            "sidecar_status": STATUS,
        },
    )
    record = shard_to_record(shard)
    record.update(
        {
            "candidate_id": chunk.candidate_id,
            "anchor_vector": anchor,
            "source_path": chunk.source_path,
            "line_start": chunk.line_range[0],
            "line_end": chunk.line_range[1],
            "provenance": _provenance(chunk.source_path, chunk.line_range),
            "trust_level": "unverified_fixture",
            "version_status": "fixture_current",
        }
    )
    return record


def _geometry_mark_record(chunk: OpenClawMemoryChunk) -> dict[str, object]:
    mark = _geometry_mark(chunk)
    record = gravity_mark_to_record(mark)
    anchor = _chunk_anchor_vector(chunk)
    record.update(
        {
            "profile": DEFAULT_PROFILE,
            "geometry_profile": DEFAULT_PROFILE,
            "anchor_vector": anchor,
            "layout_method": LAYOUT_METHOD,
            "source_role": _public_source_role(chunk.source_role),
            "provenance": _provenance(chunk.source_path, chunk.line_range),
            "status": STATUS,
            "placement_status": "experimental_unconfirmed",
        }
    )
    return record


def _geometry_mark(chunk: OpenClawMemoryChunk) -> GravityMark:
    anchor = _chunk_anchor_vector(chunk)
    terms = sorted(anchor.items(), key=lambda item: (-item[1], item[0]))
    primary = terms[0][0] if terms else "empty"
    secondary = terms[1][0] if len(terms) > 1 else primary
    q = _stable_bucket(primary, 9) - 4
    r = _stable_bucket(secondary, 9) - 4
    layer = {"durable_memory": 0, "daily_memory": 1, "dreams": 3}.get(chunk.source_role, 2)
    return GravityMark(
        content_id=chunk.candidate_id,
        geometry_profile=DEFAULT_PROFILE,
        chart_id=DEFAULT_CHART,
        layer=layer,
        q=q,
        r=r,
        anchor_vector=anchor,
        provenance=str(_provenance(chunk.source_path, chunk.line_range)["source_ref"]),
    )


def _mark_from_record(record: Mapping[str, object]) -> GravityMark:
    anchor = record.get("anchor_vector", {})
    if not isinstance(anchor, Mapping):
        anchor = {}
    return GravityMark(
        content_id=str(record["content_id"]),
        geometry_profile=str(record["geometry_profile"]),
        chart_id=str(record["chart_id"]),
        layer=int(record["layer"]),
        q=int(record["q"]),
        r=int(record["r"]),
        anchor_vector={str(key): float(value) for key, value in anchor.items()},
        provenance=_record_provenance_string(record.get("provenance")),
    )


def _query_well(query: str, scored: Sequence[Mapping[str, object]]) -> dict[str, object]:
    anchor = _anchor_vector(query)
    seed = None
    if scored:
        seed = max(
            scored,
            key=lambda item: (
                float(item.get("retrieval_score") or 0.0),
                _anchor_overlap(anchor, _candidate_anchor(item)),
            ),
        )
    seed_candidate = seed.get("candidate") if isinstance(seed, Mapping) else None
    seed_mark = seed.get("geometry_mark") if isinstance(seed, Mapping) else None
    if not isinstance(seed_mark, Mapping):
        q = 0
        r = 0
        layer = 0
    else:
        q = int(seed_mark.get("q") or 0)
        r = int(seed_mark.get("r") or 0)
        layer = int(seed_mark.get("layer") or 0)
    digest = _sha256_text("query:" + " ".join(sorted(anchor)))
    return {
        "well_id": f"well_{digest[:16]}",
        "entry_query": query,
        "geometry_profile": DEFAULT_PROFILE,
        "chart_id": DEFAULT_CHART,
        "layer": layer,
        "q": q,
        "r": r,
        "anchor_vector": anchor,
        "layout_method": LAYOUT_METHOD,
        "query_seed_candidate_id": seed_candidate.get("candidate_id") if isinstance(seed_candidate, Mapping) else None,
    }


def _anchor_vector(text: str) -> dict[str, float]:
    tokens = _tokens(text)
    counts: dict[str, int] = {}
    for token in tokens:
        counts[token] = counts.get(token, 0) + 1
    if not counts:
        return {"empty": 1.0}
    total = float(sum(counts.values()))
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:8]
    return {token: round(count / total, 6) for token, count in ranked}


def _chunk_anchor_vector(chunk: OpenClawMemoryChunk) -> dict[str, float]:
    weights: dict[str, float] = {}
    for token in _tokens(chunk.text):
        weights[token] = weights.get(token, 0.0) + 1.0
    for heading in chunk.heading_path:
        for token in _tokens(heading):
            weights[token] = weights.get(token, 0.0) + 0.35
    role_token = _public_source_role(chunk.source_role)
    weights[role_token] = weights.get(role_token, 0.0) + 0.25
    if not weights:
        return {"empty": 1.0}
    total = sum(weights.values())
    ranked = sorted(weights.items(), key=lambda item: (-item[1], item[0]))[:12]
    return {token: round(weight / total, 6) for token, weight in ranked}


def _lexical_score(query: str, text: str) -> float:
    query_tokens = set(_tokens(query))
    text_tokens = set(_tokens(text))
    if not query_tokens or not text_tokens:
        return 0.0
    overlap = len(query_tokens & text_tokens)
    coverage = overlap / len(query_tokens)
    precision = overlap / len(text_tokens)
    return round((coverage * 0.8) + (precision * 0.2), 6)


def _tokens(text: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[a-z0-9_]+", text.lower())
        if token not in _STOPWORDS and len(token) > 1
    ]


_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "be",
    "by",
    "for",
    "from",
    "has",
    "in",
    "is",
    "it",
    "md",
    "not",
    "of",
    "or",
    "source",
    "that",
    "the",
    "this",
    "to",
    "with",
}


def _gravity_report(query: str, well: Mapping[str, object], item: Mapping[str, object]) -> dict[str, object]:
    candidate = item["candidate"]
    mark = item["geometry_mark"]
    if not isinstance(candidate, Mapping) or not isinstance(mark, Mapping):
        raise ValueError("candidate and geometry_mark must be mappings")
    query_anchor = well.get("anchor_vector")
    if not isinstance(query_anchor, Mapping):
        query_anchor = {}
    mark_anchor = mark.get("anchor_vector")
    if not isinstance(mark_anchor, Mapping):
        mark_anchor = {}
    q_anchor = {str(key): float(value) for key, value in query_anchor.items()}
    c_anchor = {str(key): float(value) for key, value in mark_anchor.items()}
    overlap = _anchor_overlap(q_anchor, c_anchor)
    similarity = _cosine(q_anchor, c_anchor)
    r_column = abs(int(mark.get("q") or 0) - int(well.get("q") or 0)) + abs(int(mark.get("r") or 0) - int(well.get("r") or 0))
    scale_delta = abs(int(mark.get("layer") or 0) - int(well.get("layer") or 0))
    retrieval = float(item.get("retrieval_score") or 0.0)
    source_role = _public_source_role(str(candidate.get("source_role") or "unknown"))
    drift = _classify_semantic_drift(
        retrieval_score=retrieval,
        anchor_overlap=overlap,
        source_role=source_role,
        query=query,
        candidate_text=str(candidate.get("text") or ""),
        scale_delta=scale_delta,
    )
    return {
        "R_column_ring": r_column,
        "S_scale_delta": scale_delta,
        "A_anchor_similarity": round(similarity, 12),
        "drift_class": drift,
        "projection_method": "query_conditioned_anchor_overlap",
        "layout_method": LAYOUT_METHOD,
        "anchor_overlap": round(overlap, 12),
        "query_seed_candidate_id": well.get("query_seed_candidate_id"),
        "source_role": source_role,
        "status": "experimental_internal_only",
        "well_id": well.get("well_id"),
        "content_id": candidate.get("candidate_id"),
    }


def _classify_semantic_drift(
    *,
    retrieval_score: float,
    anchor_overlap: float,
    source_role: str,
    query: str,
    candidate_text: str,
    scale_delta: int,
) -> str:
    conflict = _has_owner_conflict(query, candidate_text)
    if retrieval_score <= 0.0 or anchor_overlap <= 0.0:
        return "semantic_break"
    if source_role == "dream" and (conflict or retrieval_score < 0.55):
        return "far_weak"
    if retrieval_score >= 0.72 and anchor_overlap >= 0.45 and scale_delta <= 1:
        return "core"
    if retrieval_score >= 0.55 and anchor_overlap >= 0.25:
        return "halo"
    if retrieval_score >= 0.35 and anchor_overlap >= 0.15:
        return "near_drift"
    if retrieval_score >= 0.15:
        return "far_coherent"
    return "far_weak"


def _has_owner_conflict(query: str, text: str) -> bool:
    q = " ".join(_tokens(query))
    t = " ".join(_tokens(text))
    ownership_query = "owner" in q or "owns" in q or "ownership" in q
    speculative_text = "not evidence" in t or "speculative" in t or "exploratory" in t
    return ownership_query and speculative_text


def _anchor_overlap(left: Mapping[str, float], right: Mapping[str, float]) -> float:
    left_keys = set(left)
    if not left_keys:
        return 0.0
    return len(left_keys & set(right)) / len(left_keys)


def _candidate_anchor(item: Mapping[str, object]) -> Mapping[str, float]:
    mark = item.get("geometry_mark")
    if isinstance(mark, Mapping) and isinstance(mark.get("anchor_vector"), Mapping):
        return {str(key): float(value) for key, value in mark["anchor_vector"].items()}  # type: ignore[index]
    return {}


def _cosine(left: Mapping[str, float], right: Mapping[str, float]) -> float:
    if not left or not right:
        return 0.0
    dot = sum(left.get(key, 0.0) * right.get(key, 0.0) for key in set(left) | set(right))
    left_norm = sum(value * value for value in left.values()) ** 0.5
    right_norm = sum(value * value for value in right.values()) ** 0.5
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def _stable_bucket(value: str, modulo: int) -> int:
    return int(_sha256_text(value)[:8], 16) % modulo


def _search_result_record(item: Mapping[str, object]) -> dict[str, object]:
    candidate = item["candidate"]
    shard = item["shard"]
    if not isinstance(candidate, Mapping):
        raise ValueError("candidate must be a mapping")
    if not isinstance(shard, Mapping):
        raise ValueError("shard must be a mapping")
    return {
        "memory_id": candidate["memory_id"],
        "candidate_id": candidate["candidate_id"],
        "shard_id": shard["shard_id"],
        "source_path": candidate["source_path"],
        "line_start": candidate["line_start"],
        "line_end": candidate["line_end"],
        "line_range": candidate["line_range"],
        "provenance": candidate["provenance"],
        "heading_path": candidate["heading_path"],
        "text": candidate["text"],
        "source_role": candidate["source_role"],
        "source_kind": candidate["source_kind"],
        "retrieval_score": item["retrieval_score"],
        "geometry_mark": item["geometry_mark"],
        "gravity_report": item["gravity_report"],
        "llm_use_hint": _llm_use_hint(str(item["gravity_report"]["drift_class"])),  # type: ignore[index]
        "trust_level": candidate["trust_level"],
        "version_status": candidate["version_status"],
    }


def _recall_item(result: Mapping[str, object]) -> dict[str, object]:
    return {
        "candidate_id": result["candidate_id"],
        "memory_id": result["memory_id"],
        "shard_id": result["shard_id"],
        "source_path": result["source_path"],
        "source_role": _public_source_role(str(result.get("source_role") or "unknown")),
        "line_range": result["line_range"],
        "text_excerpt": result["text"],
        "retrieval_score": result["retrieval_score"],
        "gravity_report": result["gravity_report"],
        "provenance": result["provenance"],
    }


def _llm_use_hint(drift_class: str) -> str:
    hints = {
        "core": "close context; verify source before use",
        "halo": "nearby context; useful with provenance",
        "near_drift": "lateral association; use cautiously",
        "far_coherent": "distant but coherent; useful lateral discovery if sourced",
        "far_weak": "weak distant relation; usually ignore or mark uncertain",
        "semantic_break": "semantic mismatch; treat cautiously",
        "chart_jump": "chart crossing; exploratory only",
        "unglued": "weak geometry relation; exploratory only",
    }
    return hints.get(drift_class, "unknown drift class; verify manually")


def _find_candidate(
    candidates: Sequence[Mapping[str, object]],
    shards: Sequence[Mapping[str, object]],
    item_id: str,
) -> Mapping[str, object] | None:
    shard_to_candidate = {str(shard["shard_id"]): str(shard["candidate_id"]) for shard in shards}
    candidate_id = shard_to_candidate.get(item_id, item_id)
    for candidate in candidates:
        if candidate.get("candidate_id") == candidate_id or candidate.get("memory_id") == candidate_id:
            return candidate
    return None


def _last_search_item(out: Path, candidate_id: str) -> Mapping[str, object] | None:
    last = out / "last_search_report.json"
    if not last.exists():
        return None
    report = _read_json(last)
    results = report.get("results", [])
    if not isinstance(results, Sequence):
        return None
    for item in results:
        if isinstance(item, Mapping) and item.get("candidate_id") == candidate_id:
            return item
    return None


def _commit_rejection(candidate_id: str, reason: str) -> dict[str, object]:
    return {
        "schema": COMMIT_SCHEMA,
        "ok": False,
        "status": STATUS,
        "candidate_id": candidate_id,
        "error": reason,
        "durable_write": False,
        "target_files_mutated": False,
        "forbidden_semantics": dict(FORBIDDEN_SEMANTICS),
    }


def _managed_entry_text(text: str, *, source: str, reason: str) -> str:
    normalized = " ".join(text.strip().split())
    return (
        f"- {normalized}\n"
        f"  - nollm_source: {source.strip()}\n"
        f"  - nollm_reason: {reason.strip()}\n"
        f"  - nollm_commit: explicit_confirmation\n"
    )


def _today_utc() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _require_path_under(root: Path, target: Path) -> None:
    root_resolved = root.resolve()
    target_resolved = target.resolve()
    try:
        target_resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError("target path escapes workspace") from exc


def _public_source_role(source_role: str) -> str:
    return {
        "durable_memory": "durable",
        "daily_memory": "daily",
        "dreams": "dream",
    }.get(source_role, source_role)


def _sidecar_manifest(
    repo: Path,
    workspace: Path,
    out: Path,
    index: OpenClawMemoryIndex,
    candidates: Sequence[Mapping[str, object]],
    shards: Sequence[Mapping[str, object]],
    marks: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    profile = default_geometry_profile()
    return {
        "schema": SIDECAR_SCHEMA,
        "status": STATUS,
        "workspace": _display_path(repo, workspace),
        "out_dir": _display_path(repo, out),
        "source_files": list(index.source_files),
        "source_roles_present": _source_roles_present(candidates),
        "accepted_get_id_forms": ["candidate_id", "memory_id", "shard_id"],
        "durable_memory_mutation": False,
        "files": {
            "candidates": "candidates.jsonl",
            "shards": "shards.jsonl",
            "geometry_marks": "geometry_marks.jsonl",
            "pending_writes": "pending_writes.jsonl",
            "sidecar_report": "openclaw_memory_sidecar_report.json",
        },
        "counts": {
            "candidates": len(candidates),
            "shards": len(shards),
            "geometry_marks": len(marks),
        },
        "geometry_profile": {
            "profile_id": profile.profile_id,
            "beta": profile.beta,
            "theta_deg": profile.theta_deg,
        },
        "forbidden_semantics": dict(FORBIDDEN_SEMANTICS),
    }


def _provenance(source_path: str, line_range: tuple[int, int]) -> dict[str, object]:
    return {
        "source_path": source_path,
        "line_start": line_range[0],
        "line_end": line_range[1],
        "source_ref": f"{source_path}:{line_range[0]}-{line_range[1]}",
    }


def _shard_id(candidate_id: str, chunk_sha256: str) -> str:
    return f"shard_{_sha256_text(candidate_id + ':' + chunk_sha256)[:16]}"


def _source_roles_present(records: Sequence[Mapping[str, object]]) -> list[str]:
    preferred = ["durable_memory", "daily_memory", "dreams", "unknown"]
    present = {str(record.get("source_role", "")) for record in records}
    return [role for role in preferred if role in present]


def _record_provenance_string(value: object) -> str | None:
    if isinstance(value, Mapping):
        source_ref = value.get("source_ref")
        return str(source_ref) if source_ref else None
    if isinstance(value, str) and value:
        return value
    return None


def _memory_id(source_path: str, line_range: tuple[int, int], chunk_sha256: str) -> str:
    raw = f"{source_path}:{line_range[0]}-{line_range[1]}:{chunk_sha256}"
    return f"mem_{_sha256_text(raw)[:16]}"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _relative_posix(base: Path, target: Path) -> str:
    return target.resolve().relative_to(base.resolve()).as_posix()


def _display_path(repo: Path, path: Path) -> str:
    try:
        return _relative_posix(repo, path)
    except ValueError:
        return str(path)


def _write_json(path: Path, report: Mapping[str, object]) -> None:
    _assert_json_primitive(report)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_jsonl(path: Path, records: Iterable[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for record in records:
        _assert_json_primitive(record)
        lines.append(json.dumps(record, sort_keys=True))
    path.write_text("".join(f"{line}\n" for line in lines), encoding="utf-8", newline="\n")


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _assert_json_primitive(value: object) -> None:
    if value is None or isinstance(value, (str, int, float, bool)):
        return
    if isinstance(value, list):
        for item in value:
            _assert_json_primitive(item)
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("report keys must be strings")
            _assert_json_primitive(item)
        return
    raise TypeError(f"report value is not JSON primitive: {type(value).__name__}")


__all__ = [
    "FORBIDDEN_SEMANTICS",
    "GET_SCHEMA",
    "COMMIT_SCHEMA",
    "RECALL_SCHEMA",
    "SCHEMA",
    "SEARCH_SCHEMA",
    "SIDECAR_SCHEMA",
    "STATUS_SCHEMA",
    "WRITE_SCHEMA",
    "OpenClawMemoryChunk",
    "OpenClawMemoryIndex",
    "build_openclaw_memory_fixture_report",
    "build_sidecar_store",
    "commit_candidate",
    "get_sidecar_item",
    "parse_openclaw_memory_workspace",
    "recall_sidecar",
    "search_sidecar",
    "sidecar_status",
    "write_candidate",
    "write_openclaw_memory_fixture_report",
    "remember_native_companion_memory",
    "recall_native_companion_memory",
    "get_native_companion_memory",
]
