from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping, Sequence


FIELD_SCHEMA = "nollm.dream_cortex_field.v1"
SNAPSHOT_SCHEMA = "nollm.source_snapshot.v1"
DREAMER_CONTRACT_SCHEMA = "nollm.dreamer_contract_fixture.v1"
ORIENT_SCHEMA = "nollm.cortex.orient.v1"
SURFACE_SCHEMA = "nollm.cortex.surface.v1"
FOCUS_SCHEMA = "nollm.cortex.focus.v1"
DRIFT_SCHEMA = "nollm.cortex.drift_return.v1"
READ_SCHEMA = "nollm.cortex.read.v1"
DIGEST_SCHEMA = "nollm.cortex.recall_digest.v1"
DEMO_SCHEMA = "nollm.dream_cortex_demo_report.v1"

SOURCE_GLOBS = ("MEMORY.md", "DREAMS.md", "memory/*.md")
SHARD_STATUSES = {"source_backed", "derived", "tentative", "superseded"}
SHARD_SCALES = {"coarse", "bridge", "fine"}
FORBIDDEN_RECALL_SEMANTICS = {
    "embedding_api": False,
    "vector_db": False,
    "sqlite_recall_path": False,
    "raw_markdown_top_k": False,
    "aliases_primary_index": False,
    "memory_file_write": False,
    "drift_trust_mapping": False,
    "hard_drift_rejection": False,
}


@dataclass(frozen=True)
class SourceFileSnapshot:
    source_path: str
    sha256: str
    byte_count: int
    read_timestamp_utc: str

    def to_record(self) -> dict[str, object]:
        return {
            "source_path": self.source_path,
            "sha256": self.sha256,
            "byte_count": self.byte_count,
            "read_timestamp_utc": self.read_timestamp_utc,
        }


def source_snapshot(workspace: Path | str) -> dict[str, object]:
    root = Path(workspace).resolve()
    files = [item.to_record() for item in _snapshot_files(root)]
    return {
        "schema": SNAPSHOT_SCHEMA,
        "workspace": str(root),
        "source_globs": list(SOURCE_GLOBS),
        "source_files": files,
        "source_file_count": len(files),
        "read_only": True,
        "forbidden_recall_semantics": dict(FORBIDDEN_RECALL_SEMANTICS),
    }


def ingest_dreamer_fixture(
    workspace: Path | str,
    dreamer_output: Path | str,
    out_dir: Path | str,
) -> dict[str, object]:
    root = Path(workspace).resolve()
    output_path = Path(dreamer_output).resolve()
    out = Path(out_dir).resolve()
    snapshot = source_snapshot(root)
    dream = _read_json(output_path)
    _validate_dreamer_output(dream)
    _validate_source_links(snapshot, dream)
    field = {
        "schema": FIELD_SCHEMA,
        "field_id": str(dream.get("field_id")),
        "source_snapshot": snapshot,
        "dreamer_output_path": str(output_path),
        "charts": dream.get("charts", []),
        "shards": _sorted_shards(dream.get("shards", [])),
        "relations": sorted(dream.get("relations", []), key=lambda item: (str(item.get("from")), str(item.get("to")))),
        "projection": {
            "method": "fixture_dreamer_projection",
            "llm_provider_call": False,
            "source_files_mutated": False,
            "recall_unit": "dream_shard",
            "raw_markdown_chunks_are_recall_units": False,
        },
        "forbidden_recall_semantics": dict(FORBIDDEN_RECALL_SEMANTICS),
    }
    out.mkdir(parents=True, exist_ok=True)
    _write_json(out / "source_snapshot.json", snapshot)
    _write_json(out / "dream_field.json", field)
    report = {
        "schema": FIELD_SCHEMA,
        "ok": True,
        "field_id": field["field_id"],
        "out_dir": str(out),
        "source_file_count": snapshot["source_file_count"],
        "shard_count": len(field["shards"]),
        "source_files_mutated": False,
        "forbidden_recall_semantics": dict(FORBIDDEN_RECALL_SEMANTICS),
    }
    _write_json(out / "ingest_report.json", report)
    return report


def nollm_orient(out_dir: Path | str, *, query: str, limit: int = 3) -> dict[str, object]:
    field = _load_field(out_dir)
    pulse = _entry_pulse(query)
    surfaces = []
    for shard in _shards(field, scale="coarse"):
        score = _pulse_overlap(pulse, _shard_terms(shard))
        if score > 0.0:
            surfaces.append(
                {
                    "surface_id": shard["shard_id"],
                    "scale": "coarse",
                    "text": shard["text"],
                    "coverage": shard.get("coverage", {}),
                    "placement": shard["placement"],
                    "entry_overlap": score,
                    "status": shard["status"],
                    "source_links": shard.get("source_links", []),
                }
            )
    surfaces.sort(key=lambda item: (-float(item["entry_overlap"]), str(item["surface_id"])))
    report = {
        "schema": ORIENT_SCHEMA,
        "ok": True,
        "query": query,
        "entry_pulse": sorted(pulse),
        "orientation_mode": "bounded_coarse_surface",
        "not_alias_top_k": True,
        "surfaces": surfaces[: max(1, limit)],
        "none": not surfaces,
        "forbidden_recall_semantics": dict(FORBIDDEN_RECALL_SEMANTICS),
    }
    _write_json(Path(out_dir).resolve() / "last_orient_report.json", report)
    return report


def nollm_surface(out_dir: Path | str, *, surface_id: str) -> dict[str, object]:
    field = _load_field(out_dir)
    surface = _find_shard(field, surface_id)
    if surface is None or surface.get("scale") != "coarse":
        return _not_found(SURFACE_SCHEMA, surface_id)
    cells = [surface]
    for relation in _relations_from(field, surface_id, kinds={"contains", "bridges_to", "lateral_to"}):
        target = _find_shard(field, str(relation["to"]))
        if target is not None and target.get("scale") in {"bridge", "coarse"}:
            cells.append(target)
    report = {
        "schema": SURFACE_SCHEMA,
        "ok": True,
        "surface_id": surface_id,
        "cells": [_public_shard(item) for item in _unique_shards(cells)],
        "content_bearing": True,
        "primary_path": [item["shard_id"] for item in cells if item.get("scale") != "coarse"],
        "forbidden_recall_semantics": dict(FORBIDDEN_RECALL_SEMANTICS),
    }
    _write_json(Path(out_dir).resolve() / "last_surface_report.json", report)
    return report


def nollm_focus(out_dir: Path | str, *, query: str, surface_id: str, sufficient_scale: int = 2) -> dict[str, object]:
    field = _load_field(out_dir)
    pulse = _entry_pulse(query)
    surface = _find_shard(field, surface_id)
    if surface is None:
        return _not_found(FOCUS_SCHEMA, surface_id)
    candidates: list[dict[str, object]] = []
    for relation in _relations_from(field, surface_id, kinds={"contains", "bridges_to"}):
        target = _find_shard(field, str(relation["to"]))
        if target is None:
            continue
        overlap = _pulse_overlap(pulse, _shard_terms(target))
        coverage = float(target.get("coverage", {}).get("specificity", 0.0)) if isinstance(target.get("coverage"), Mapping) else 0.0
        sufficient = _scale_number(str(target.get("scale"))) >= sufficient_scale or (overlap >= 0.34 and coverage >= 0.5)
        candidates.append(
            {
                **_public_shard(target),
                "entry_overlap": overlap,
                "sufficient": sufficient,
                "relation": relation.get("kind"),
            }
        )
    candidates.sort(key=lambda item: (-float(item["entry_overlap"]), -int(bool(item["sufficient"])), str(item["shard_id"])))
    selected = next((item for item in candidates if item["sufficient"]), candidates[0] if candidates else None)
    report = {
        "schema": FOCUS_SCHEMA,
        "ok": True,
        "query": query,
        "surface_id": surface_id,
        "sufficient_scale": sufficient_scale,
        "selected": selected,
        "visited": candidates,
        "stopped_at_sufficient_scale": selected is not None,
        "raw_span_descent_required": False,
        "forbidden_recall_semantics": dict(FORBIDDEN_RECALL_SEMANTICS),
    }
    _write_json(Path(out_dir).resolve() / "last_focus_report.json", report)
    return report


def nollm_drift(out_dir: Path | str, *, shard_id: str, query: str = "") -> dict[str, object]:
    field = _load_field(out_dir)
    if _find_shard(field, shard_id) is None:
        return _not_found(DRIFT_SCHEMA, shard_id)
    pulse = _entry_pulse(query)
    lateral = []
    for relation in _relations_from(field, shard_id, kinds={"lateral_to", "returns_to"}):
        target = _find_shard(field, str(relation["to"]))
        if target is None:
            continue
        lateral.append(
            {
                **_public_shard(target),
                "drift": relation.get("drift", "far_coherent"),
                "label": "return" if relation.get("kind") == "returns_to" else "lateral",
                "entry_overlap": _pulse_overlap(pulse, _shard_terms(target)) if pulse else 0.0,
            }
        )
    report = {
        "schema": DRIFT_SCHEMA,
        "ok": True,
        "shard_id": shard_id,
        "lateral": [item for item in lateral if item["label"] == "lateral"],
        "return": next((item for item in lateral if item["label"] == "return"), None),
        "return_instruction": "Return to the entry task after inspecting useful lateral context.",
        "hard_drift_rejection": False,
        "forbidden_recall_semantics": dict(FORBIDDEN_RECALL_SEMANTICS),
    }
    _write_json(Path(out_dir).resolve() / "last_drift_report.json", report)
    return report


def nollm_read(out_dir: Path | str, *, shard_id: str) -> dict[str, object]:
    field = _load_field(out_dir)
    shard = _find_shard(field, shard_id)
    if shard is None:
        return _not_found(READ_SCHEMA, shard_id)
    report = {
        "schema": READ_SCHEMA,
        "ok": True,
        "shard": _public_shard(shard),
        "read_unit": "dream_shard",
        "raw_source_chunk": False,
        "forbidden_recall_semantics": dict(FORBIDDEN_RECALL_SEMANTICS),
    }
    _write_json(Path(out_dir).resolve() / "last_read_report.json", report)
    return report


def nollm_compose_digest(out_dir: Path | str, *, query: str) -> dict[str, object]:
    orient = nollm_orient(out_dir, query=query)
    if orient["none"]:
        digest = {
            "schema": DIGEST_SCHEMA,
            "ok": True,
            "query": query,
            "nollm_recall_digest": "NONE",
            "primary": [],
            "lateral": [],
            "cautions": ["The dream field lacks useful material for this entry task."],
            "return": {"instruction": "Return NONE to the host; do not invent memory."},
            "forbidden_recall_semantics": dict(FORBIDDEN_RECALL_SEMANTICS),
        }
        _write_json(Path(out_dir).resolve() / "last_recall_digest.json", digest)
        return digest
    surface_id = str(orient["surfaces"][0]["surface_id"])  # type: ignore[index]
    surface = nollm_surface(out_dir, surface_id=surface_id)
    focus = nollm_focus(out_dir, query=query, surface_id=surface_id)
    selected = focus.get("selected")
    selected_id = str(selected.get("shard_id")) if isinstance(selected, Mapping) and selected.get("shard_id") else surface_id
    drift = nollm_drift(out_dir, shard_id=selected_id, query=query)
    primary = [selected] if isinstance(selected, Mapping) else surface.get("cells", [])[:1]
    lateral = drift.get("lateral", [])
    digest = {
        "schema": DIGEST_SCHEMA,
        "ok": True,
        "query": query,
        "entry": {
            "task_view": query,
            "starting_surface": [surface_id],
            "orientation_mode": "coarse_surface_first",
        },
        "sufficient_scale": _scale_number(str(primary[0].get("scale"))) if primary else 1,  # type: ignore[index]
        "primary": primary,
        "lateral": lateral,
        "return": {
            "instruction": "Return to the original user task; use lateral material only as labelled context.",
            "from_shard_id": selected_id,
        },
        "cautions": _digest_cautions(primary, lateral),
        "nollm_recall_digest": "READY",
        "forbidden_recall_semantics": dict(FORBIDDEN_RECALL_SEMANTICS),
    }
    _write_json(Path(out_dir).resolve() / "last_recall_digest.json", digest)
    return digest


def run_demo_report(workspace: Path | str, dreamer_output: Path | str, out_dir: Path | str) -> dict[str, object]:
    before = source_snapshot(workspace)
    ingest = dict(ingest_dreamer_fixture(workspace, dreamer_output, out_dir))
    ingest.pop("out_dir", None)
    cases = {
        "orientation": nollm_orient(out_dir, query="OpenClaw Active Memory 作为 Cortex 如何使用 Nollm?"),
        "focus": nollm_focus(out_dir, query="OpenClaw Active Memory Cortex recall spine", surface_id="surface_openclaw_nollm"),
        "lateral": nollm_drift(out_dir, shard_id="bridge_active_memory_cortex", query="OpenClaw Cortex"),
        "mixed_language_digest": nollm_compose_digest(out_dir, query="Nollm 和 OpenClaw memory-core 的边界是什么?"),
        "unrelated": nollm_compose_digest(out_dir, query="咖啡机保修编号是多少?"),
    }
    after = source_snapshot(workspace)
    report = {
        "schema": DEMO_SCHEMA,
        "ok": True,
        "ingest": ingest,
        "cases": cases,
        "source_files_byte_identical_after_projection": _snapshot_hashes(before) == _snapshot_hashes(after),
        "source_files_before": _snapshot_hashes(before),
        "source_files_after": _snapshot_hashes(after),
        "forbidden_recall_semantics": dict(FORBIDDEN_RECALL_SEMANTICS),
    }
    _write_json(Path(out_dir).resolve() / "dream_cortex_demo_report.json", report)
    return report


def _snapshot_files(root: Path) -> list[SourceFileSnapshot]:
    paths: list[Path] = []
    for pattern in SOURCE_GLOBS:
        paths.extend(sorted(path for path in root.glob(pattern) if path.is_file()))
    unique = sorted(set(paths), key=lambda path: path.relative_to(root).as_posix())
    records: list[SourceFileSnapshot] = []
    for path in unique:
        data = path.read_bytes()
        stat = path.stat()
        records.append(
            SourceFileSnapshot(
                source_path=path.relative_to(root).as_posix(),
                sha256=hashlib.sha256(data).hexdigest(),
                byte_count=len(data),
                read_timestamp_utc=datetime.fromtimestamp(stat.st_mtime, timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            )
        )
    return records


def _validate_dreamer_output(record: Mapping[str, object]) -> None:
    if record.get("schema") != DREAMER_CONTRACT_SCHEMA:
        raise ValueError("dreamer fixture schema mismatch")
    shards = record.get("shards")
    if not isinstance(shards, list) or not shards:
        raise ValueError("dreamer output requires shards")
    seen: set[str] = set()
    for shard in shards:
        if not isinstance(shard, Mapping):
            raise ValueError("shard must be a mapping")
        shard_id = _required_str(shard, "shard_id")
        if shard_id in seen:
            raise ValueError("duplicate shard_id")
        seen.add(shard_id)
        if shard.get("status") not in SHARD_STATUSES:
            raise ValueError(f"unsupported shard status: {shard.get('status')}")
        if shard.get("scale") not in SHARD_SCALES:
            raise ValueError(f"unsupported shard scale: {shard.get('scale')}")
        _required_str(shard, "text")
        placement = shard.get("placement")
        if not isinstance(placement, Mapping):
            raise ValueError("shard placement must be a mapping")


def _validate_source_links(snapshot: Mapping[str, object], dream: Mapping[str, object]) -> None:
    hashes = {
        str(item["source_path"]): str(item["sha256"])
        for item in snapshot.get("source_files", [])
        if isinstance(item, Mapping)
    }
    for shard in dream.get("shards", []):
        if not isinstance(shard, Mapping):
            continue
        for link in shard.get("source_links", []):
            if not isinstance(link, Mapping):
                raise ValueError("source link must be a mapping")
            path = _required_str(link, "source_path")
            if path not in hashes:
                raise ValueError(f"source link points outside snapshot: {path}")
            expected = link.get("source_sha256")
            if expected is not None and expected != hashes[path]:
                raise ValueError(f"source hash mismatch for {path}")


def _load_field(out_dir: Path | str) -> dict[str, object]:
    path = Path(out_dir).resolve() / "dream_field.json"
    if not path.exists():
        raise FileNotFoundError("dream field is missing; run ingest first")
    field = _read_json(path)
    if field.get("schema") != FIELD_SCHEMA:
        raise ValueError("dream field schema mismatch")
    return field


def _shards(field: Mapping[str, object], *, scale: str | None = None) -> list[dict[str, object]]:
    shards = [dict(item) for item in field.get("shards", []) if isinstance(item, Mapping)]
    if scale is not None:
        shards = [item for item in shards if item.get("scale") == scale]
    return shards


def _find_shard(field: Mapping[str, object], shard_id: str) -> dict[str, object] | None:
    for shard in _shards(field):
        if shard.get("shard_id") == shard_id:
            return shard
    return None


def _relations_from(field: Mapping[str, object], shard_id: str, *, kinds: set[str]) -> list[dict[str, object]]:
    return [
        dict(item)
        for item in field.get("relations", [])
        if isinstance(item, Mapping) and item.get("from") == shard_id and item.get("kind") in kinds
    ]


def _entry_pulse(query: str) -> set[str]:
    return set(_tokens(query))


def _shard_terms(shard: Mapping[str, object]) -> set[str]:
    terms = set(_tokens(str(shard.get("text", ""))))
    for item in shard.get("anchors", []):
        terms.update(_tokens(str(item)))
    return terms


def _tokens(text: str) -> list[str]:
    latin = re.findall(r"[a-z0-9_]+", text.lower())
    cjk = re.findall(r"[\u4e00-\u9fff]", text)
    cjk_bigrams = ["".join(pair) for pair in zip(cjk, cjk[1:])]
    tokens = latin + cjk + cjk_bigrams
    return [token for token in tokens if token not in _STOPWORDS and len(token) > 0]


def _pulse_overlap(pulse: set[str], terms: set[str]) -> float:
    if not pulse or not terms:
        return 0.0
    return round(len(pulse & terms) / len(pulse), 6)


def _scale_number(scale: str) -> int:
    return {"coarse": 1, "bridge": 2, "fine": 3}.get(scale, 0)


def _public_shard(shard: Mapping[str, object]) -> dict[str, object]:
    return {
        "shard_id": shard["shard_id"],
        "scale": shard["scale"],
        "text": shard["text"],
        "status": shard["status"],
        "placement": shard["placement"],
        "coverage": shard.get("coverage", {}),
        "source_links": shard.get("source_links", []),
        "source_trace_kind": shard.get("source_trace_kind", "none"),
    }


def _unique_shards(shards: Iterable[Mapping[str, object]]) -> list[Mapping[str, object]]:
    seen: set[str] = set()
    result = []
    for shard in shards:
        shard_id = str(shard["shard_id"])
        if shard_id not in seen:
            seen.add(shard_id)
            result.append(shard)
    return result


def _digest_cautions(primary: Sequence[object], lateral: object) -> list[str]:
    cautions = ["Do not treat drift labels as trust/status or as a hard rejection rule."]
    if lateral:
        cautions.append("Lateral findings are context, not primary evidence.")
    for item in primary:
        if isinstance(item, Mapping) and item.get("status") in {"derived", "tentative"}:
            cautions.append("Derived or tentative shards should be used as orientation, not source truth.")
    return sorted(set(cautions))


def _not_found(schema: str, item_id: str) -> dict[str, object]:
    return {
        "schema": schema,
        "ok": False,
        "id": item_id,
        "error": "not_found",
        "forbidden_recall_semantics": dict(FORBIDDEN_RECALL_SEMANTICS),
    }


def _snapshot_hashes(snapshot: Mapping[str, object]) -> dict[str, str]:
    return {
        str(item["source_path"]): str(item["sha256"])
        for item in snapshot.get("source_files", [])
        if isinstance(item, Mapping)
    }


def _sorted_shards(items: object) -> list[dict[str, object]]:
    if not isinstance(items, list):
        raise ValueError("shards must be a list")
    return sorted((dict(item) for item in items if isinstance(item, Mapping)), key=lambda item: str(item["shard_id"]))


def _required_str(record: Mapping[str, object], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


_STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "for",
    "from",
    "in",
    "is",
    "of",
    "or",
    "the",
    "to",
    "with",
    "what",
    "how",
    "this",
    "that",
    "md",
    "的",
    "了",
    "是",
    "和",
    "在",
    "吗",
    "么",
}


__all__ = [
    "DEMO_SCHEMA",
    "DIGEST_SCHEMA",
    "DREAMER_CONTRACT_SCHEMA",
    "FIELD_SCHEMA",
    "FORBIDDEN_RECALL_SEMANTICS",
    "FOCUS_SCHEMA",
    "ORIENT_SCHEMA",
    "READ_SCHEMA",
    "SNAPSHOT_SCHEMA",
    "SURFACE_SCHEMA",
    "DRIFT_SCHEMA",
    "ingest_dreamer_fixture",
    "nollm_compose_digest",
    "nollm_drift",
    "nollm_focus",
    "nollm_orient",
    "nollm_read",
    "nollm_surface",
    "run_demo_report",
    "source_snapshot",
]
