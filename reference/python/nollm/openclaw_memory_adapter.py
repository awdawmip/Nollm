from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from nollm.dream_shard import DreamShard, shard_to_record
from nollm.geometry_profiles import default_geometry_profile
from nollm.gravity import (
    GravityMark,
    GravityWell,
    create_gravity_report,
    gravity_mark_to_record,
    gravity_report_to_record,
    gravity_well_to_record,
)


SCHEMA = "nollm.openclaw_memory_fixture_index.v1"
SIDECAR_SCHEMA = "nollm.openclaw_memory_sidecar.v1"
SEARCH_SCHEMA = "nollm.openclaw_memory_sidecar_search.v1"
GET_SCHEMA = "nollm.openclaw_memory_sidecar_get.v1"
STATUS_SCHEMA = "nollm.openclaw_memory_sidecar_status.v1"
WRITE_SCHEMA = "nollm.openclaw_memory_sidecar_write_candidate.v1"
DEFAULT_PROFILE = "default_dream"
DEFAULT_CHART = "openclaw_memory_fixture"
STATUS = "experimental_internal_sidecar"
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
    well = _query_well(query)
    scored = []
    for candidate in candidates:
        mark = _mark_from_record(marks[str(candidate["candidate_id"])])
        gravity = gravity_report_to_record(create_gravity_report(well, mark))
        scored.append(
            {
                "candidate": candidate,
                "retrieval_score": _lexical_score(query, str(candidate["text"])),
                "gravity_report": gravity,
                "geometry_mark": marks[str(candidate["candidate_id"])],
                "shard": shards[str(candidate["candidate_id"])],
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
    results = [_search_result_record(item) for item in scored[:limit]]
    report = {
        "schema": SEARCH_SCHEMA,
        "ok": True,
        "status": STATUS,
        "query": query,
        "limit": limit,
        "gravity_well": gravity_well_to_record(well),
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
    if not text.strip():
        raise ValueError("text must be non-empty")
    if not source.strip():
        raise ValueError("source must be non-empty")
    build_sidecar_store(repo_root, workspace, out_dir)
    out = Path(out_dir).resolve()
    pending_path = out / "pending_writes.jsonl"
    existing = _read_jsonl(pending_path)
    normalized = " ".join(text.strip().split())
    pending_id = f"pending_{_sha256_text(source + ':' + normalized)[:16]}"
    record = {
        "pending_id": pending_id,
        "text": normalized,
        "source": source,
        "status": "pending_review",
        "durable_write": False,
        "target_files_mutated": False,
        "durable_memory_mutation": False,
        "why_pending": why,
        "required_review": "explicit human approval or future configured promotion policy",
        "forbidden_semantics": dict(FORBIDDEN_SEMANTICS),
    }
    records = [item for item in existing if item.get("pending_id") != pending_id]
    records.append(record)
    records.sort(key=lambda item: str(item["pending_id"]))
    _write_jsonl(pending_path, records)
    report = {
        "schema": WRITE_SCHEMA,
        "ok": True,
        "status": STATUS,
        "candidate": record,
        "pending_count": len(records),
        "forbidden_semantics": dict(FORBIDDEN_SEMANTICS),
    }
    _write_json(out / "last_write_candidate_report.json", report)
    return report


def sidecar_status(repo_root: Path | str, workspace: Path | str, out_dir: Path | str) -> dict[str, object]:
    build_sidecar_store(repo_root, workspace, out_dir)
    repo = Path(repo_root).resolve()
    out = Path(out_dir).resolve()
    manifest = _read_json(out / "sidecar_manifest.json")
    report = {
        "schema": STATUS_SCHEMA,
        "ok": True,
        "status": STATUS,
        "workspace": manifest["workspace"],
        "out_dir": _display_path(repo, out),
        "manifest": manifest,
        "accepted_get_id_forms": ["candidate_id", "memory_id", "shard_id"],
        "source_roles_present": manifest["source_roles_present"],
        "durable_memory_mutation": False,
        "counts": {
            "candidates": len(_read_jsonl(out / "candidates.jsonl")),
            "shards": len(_read_jsonl(out / "shards.jsonl")),
            "geometry_marks": len(_read_jsonl(out / "geometry_marks.jsonl")),
            "pending_writes": len(_read_jsonl(out / "pending_writes.jsonl")),
        },
        "forbidden_semantics": dict(FORBIDDEN_SEMANTICS),
    }
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
    record.update(
        {
            "profile": DEFAULT_PROFILE,
            "geometry_profile": DEFAULT_PROFILE,
            "anchor_vector": _anchor_vector(chunk.text),
            "provenance": _provenance(chunk.source_path, chunk.line_range),
            "status": STATUS,
            "placement_status": "experimental_unconfirmed",
        }
    )
    return record


def _geometry_mark(chunk: OpenClawMemoryChunk) -> GravityMark:
    digest = _sha256_text(chunk.candidate_id + ":" + chunk.text)
    layer = int(digest[:2], 16) % 5
    q = int(digest[2:4], 16) % 9 - 4
    r = int(digest[4:6], 16) % 9 - 4
    return GravityMark(
        content_id=chunk.candidate_id,
        geometry_profile=DEFAULT_PROFILE,
        chart_id=DEFAULT_CHART,
        layer=layer,
        q=q,
        r=r,
        anchor_vector=_anchor_vector(chunk.text),
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


def _query_well(query: str) -> GravityWell:
    digest = _sha256_text("query:" + query)
    return GravityWell(
        well_id=f"well_{digest[:16]}",
        entry_query=query,
        geometry_profile=DEFAULT_PROFILE,
        chart_id=DEFAULT_CHART,
        layer=int(digest[:2], 16) % 3,
        q=int(digest[2:4], 16) % 5 - 2,
        r=int(digest[4:6], 16) % 5 - 2,
        anchor_vector=_anchor_vector(query),
    )


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


def _lexical_score(query: str, text: str) -> float:
    query_tokens = set(_tokens(query))
    text_tokens = set(_tokens(text))
    if not query_tokens or not text_tokens:
        return 0.0
    overlap = len(query_tokens & text_tokens)
    return round(overlap / len(query_tokens), 6)


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9_]+", text.lower())


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
        "retrieval_score": item["retrieval_score"],
        "geometry_mark": item["geometry_mark"],
        "gravity_report": item["gravity_report"],
        "llm_use_hint": _llm_use_hint(str(item["gravity_report"]["drift_class"])),  # type: ignore[index]
        "trust_level": candidate["trust_level"],
        "version_status": candidate["version_status"],
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
    "SCHEMA",
    "SEARCH_SCHEMA",
    "SIDECAR_SCHEMA",
    "STATUS_SCHEMA",
    "WRITE_SCHEMA",
    "OpenClawMemoryChunk",
    "OpenClawMemoryIndex",
    "build_openclaw_memory_fixture_report",
    "build_sidecar_store",
    "get_sidecar_item",
    "parse_openclaw_memory_workspace",
    "search_sidecar",
    "sidecar_status",
    "write_candidate",
    "write_openclaw_memory_fixture_report",
]
