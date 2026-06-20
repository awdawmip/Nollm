from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Mapping, Sequence

from nollm.geometry import Axial, HexAddress, axial_disk, coverage_map
from nollm.geometry_profiles import default_geometry_profile, layer_spec_from_profile
from nollm.gravity import (
    GravityMark,
    GravityWell,
    create_gravity_report,
    gravity_mark_to_record,
    gravity_report_to_record,
    gravity_well_from_record,
    gravity_well_to_record,
)


FIELD_SCHEMA = "nollm.dream_cortex_field.v3"
SNAPSHOT_SCHEMA = "nollm.source_snapshot.v1"
DREAM_PACKET_SCHEMA = "nollm.dream_packet.v1"
DREAMER_CONTRACT_SCHEMA = "nollm.dreamer_delta.v1"
OVERVIEW_SCHEMA = "nollm.cortex.field_overview.v2"
OPEN_WELL_SCHEMA = "nollm.cortex.open_well.v2"
SURFACE_SCHEMA = "nollm.cortex.surface_geometry.v3"
FOCUS_SCHEMA = "nollm.cortex.focus_geometry.v3"
DRIFT_SCHEMA = "nollm.cortex.drift_geometry.v3"
READ_SCHEMA = "nollm.cortex.read.v3"
TRACE_SCHEMA = "nollm.cortex.recall_trace.v2"
DEMO_SCHEMA = "nollm.dream_cortex_demo_report.v3"

SOURCE_GLOBS = ("MEMORY.md", "DREAMS.md", "memory/*.md")
PRIMARY_DREAM_SOURCES = ("MEMORY.md",)
MAX_DREAM_PACKET_CHARS = 12000
SHARD_STATUSES = {"source_backed", "derived", "tentative", "superseded"}
SHARD_SCALES = {"coarse", "bridge", "fine"}
SCALE_LAYERS = {"coarse": 0, "bridge": 1, "fine": 2}
FORBIDDEN_DREAMER_FIELDS = {"q", "r", "layer", "HexAddress", "rank", "score", "query", "answer", "top_k", "embedding"}
FORBIDDEN_RECALL_SEMANTICS = {
    "embedding_api": False,
    "vector_db": False,
    "sqlite_recall_path": False,
    "raw_markdown_top_k": False,
    "aliases_primary_index": False,
    "lexical_query_ranking": False,
    "core_digest_composition": False,
    "memory_file_write": False,
    "drift_trust_mapping": False,
    "hard_drift_rejection": False,
}


@dataclass(frozen=True)
class SourceFileSnapshot:
    source_path: str
    sha256: str
    byte_count: int
    line_count: int
    read_timestamp_utc: str

    def to_record(self) -> dict[str, object]:
        return {
            "source_path": self.source_path,
            "sha256": self.sha256,
            "byte_count": self.byte_count,
            "line_count": self.line_count,
            "read_timestamp_utc": self.read_timestamp_utc,
        }


def source_snapshot(workspace: Path | str) -> dict[str, object]:
    root = Path(workspace).resolve()
    files = [item.to_record() for item in _snapshot_files(root)]
    record = {
        "schema": SNAPSHOT_SCHEMA,
        "workspace": str(root),
        "source_globs": list(SOURCE_GLOBS),
        "source_files": files,
        "source_file_count": len(files),
        "read_only": True,
        "forbidden_recall_semantics": dict(FORBIDDEN_RECALL_SEMANTICS),
    }
    record["source_snapshot_hash"] = _source_snapshot_hash(record)
    return record


def build_dream_packet(
    workspace: Path | str,
    *,
    field_id: str = "openclaw-dream-field",
    current_field: Mapping[str, object] | None = None,
    max_chars: int = MAX_DREAM_PACKET_CHARS,
) -> dict[str, object]:
    root = Path(workspace).resolve()
    snapshot = source_snapshot(root)
    source_by_path = {str(item["source_path"]): item for item in snapshot.get("source_files", []) if isinstance(item, Mapping)}
    material: list[dict[str, object]] = []
    remaining = max_chars
    for source_path in PRIMARY_DREAM_SOURCES:
        record = source_by_path.get(source_path)
        if record is None:
            continue
        text = (root / source_path).read_text(encoding="utf-8")
        sections = _section_source_text(text, max_chars=max(1, remaining))
        for start_line, end_line, section_text in sections:
            if remaining <= 0:
                raise ValueError("dream packet source material exceeds configured bound")
            remaining -= len(section_text)
            material.append(
                {
                    "source_path": source_path,
                    "source_sha256": record["sha256"],
                    "line_range": [start_line, end_line],
                    "text": section_text,
                    "material_id": _sha256_text(_stable_json({"path": source_path, "sha": record["sha256"], "line_range": [start_line, end_line], "text": section_text}))[:16],
                }
            )
    packet = {
        "schema": DREAM_PACKET_SCHEMA,
        "source_snapshot_hash": snapshot["source_snapshot_hash"],
        "field_id": field_id,
        "source_material": material,
        "prior_field_summary": _prior_field_summary(current_field),
        "source_diff": {},
    }
    if not material:
        raise ValueError("dream packet requires at least one source material section")
    return packet


def ingest_dreamer_fixture(
    workspace: Path | str,
    dreamer_output: Path | str,
    out_dir: Path | str,
) -> dict[str, object]:
    delta = _read_json(Path(dreamer_output).resolve())
    return publish_dreamer_delta(workspace, out_dir, delta, dreamer_run_ref={"kind": "explicit_fixture", "path": str(Path(dreamer_output).resolve())})


def publish_dreamer_delta(
    workspace: Path | str,
    out_dir: Path | str,
    delta: Mapping[str, object],
    *,
    dreamer_run_ref: Mapping[str, object] | None = None,
    dream_packet: Mapping[str, object] | None = None,
) -> dict[str, object]:
    root = Path(workspace).resolve()
    out = Path(out_dir).resolve()
    snapshot = source_snapshot(root)
    current = _load_current_field(out)
    _validate_dreamer_delta(delta, snapshot, dream_packet=dream_packet)
    field_id = str(delta["field_id"])
    parent_revision_id = str(current["revision_id"]) if current and current.get("field_id") == field_id else None
    placed = _place_delta(delta, current)
    revision_id = _revision_id(field_id, snapshot["source_snapshot_hash"], placed, parent_revision_id)
    created_at = _created_at_from_snapshot(snapshot)
    field = {
        "schema": FIELD_SCHEMA,
        "field_id": field_id,
        "revision_id": revision_id,
        "source_snapshot_hash": snapshot["source_snapshot_hash"],
        "parent_revision_id": parent_revision_id,
        "created_at_utc": created_at,
        "geometry_profile": default_geometry_profile().profile_id,
        "chart_id": "chart_openclaw_integration",
        "source_snapshot": snapshot,
        "dreamer_run_ref": dict(dreamer_run_ref or {"kind": "mock_or_operator_supplied"}),
        "dream_packet_ref": _dream_packet_ref(dream_packet),
        "charts": [{"chart_id": "chart_openclaw_integration", "label": field_id}],
        "shards": placed,
        "gravity_marks": [_mark_record(shard) for shard in placed],
        "dreamer_intents": _dreamer_intents(delta),
        "core_placement": {
            "method": "deterministic_local_v1",
            "dreamer_coordinates_accepted": False,
            "runtime_selection": "cortex_explicit_geometry_path",
        },
        "forbidden_recall_semantics": dict(FORBIDDEN_RECALL_SEMANTICS),
    }
    _publish_revision(out, field, snapshot)
    return {
        "schema": FIELD_SCHEMA,
        "ok": True,
        "status": "published",
        "field_id": field_id,
        "revision_id": revision_id,
        "parent_revision_id": parent_revision_id,
        "source_snapshot_hash": snapshot["source_snapshot_hash"],
        "shard_count": len(placed),
        "source_files_mutated": False,
        "forbidden_recall_semantics": dict(FORBIDDEN_RECALL_SEMANTICS),
    }


def nollm_field_overview(out_dir: Path | str, *, field_id: str | None = None, limit: int = 20, workspace: Path | str | None = None) -> dict[str, object]:
    field = _load_field_report(out_dir)
    if field.get("ok") is False:
        return field
    if field_id is not None and field.get("field_id") != field_id:
        return _error(OVERVIEW_SCHEMA, "field_not_found", f"Field is not installed: {field_id}")
    shards = _shards(field)
    coarse = [item for item in shards if item.get("scale") == "coarse"]
    field_stale = False
    if workspace is not None:
        field_stale = source_snapshot(workspace)["source_snapshot_hash"] != field["source_snapshot_hash"]
    report = {
        "schema": OVERVIEW_SCHEMA,
        "ok": True,
        "field_id": field["field_id"],
        "revision_id": field["revision_id"],
        "source_snapshot_hash": field["source_snapshot_hash"],
        "field_stale": field_stale,
        "geometry_profile": field["geometry_profile"],
        "chart_id": field["chart_id"],
        "selection_role": "cortex_must_choose_entry",
        "coarse_cells": [_cell_descriptor(item) for item in coarse[: max(1, limit)]],
        "scale_availability": _scale_availability(shards),
        "query_score": None,
        "forbidden_recall_semantics": dict(FORBIDDEN_RECALL_SEMANTICS),
    }
    _write_json(Path(out_dir).resolve() / "last_field_overview.json", report)
    return report


def nollm_open_well(
    out_dir: Path | str,
    *,
    entry_shard_id: str,
    entry_task: str,
    anchor_vector: Mapping[str, float],
    revision_id: str | None = None,
    ttl_seconds: int = 3600,
    created_at_utc: str | None = None,
) -> dict[str, object]:
    field = _require_field(out_dir, revision_id=revision_id)
    _validate_anchor_vector(anchor_vector)
    entry = _require_shard(field, entry_shard_id)
    mark = _mark_from_shard(entry)
    created_at = created_at_utc or _utc_now()
    expires_at = _add_seconds(created_at, ttl_seconds)
    seed = _stable_json(
        {
            "field": str(field["field_id"]),
            "revision": str(field["revision_id"]),
            "entry": entry_shard_id,
            "task": entry_task,
            "anchor": dict(anchor_vector),
            "created_at": created_at,
        }
    )
    well = GravityWell(
        well_id=f"well_{_sha256_text(seed)[:16]}",
        entry_query=entry_task,
        geometry_profile=mark.geometry_profile,
        chart_id=mark.chart_id,
        layer=mark.layer,
        q=mark.q,
        r=mark.r,
        anchor_vector=dict(anchor_vector),
        created_at=created_at,
    )
    record = {
        "schema": OPEN_WELL_SCHEMA,
        "well_id": well.well_id,
        "field_id": field["field_id"],
        "revision_id": field["revision_id"],
        "source_snapshot_hash": field["source_snapshot_hash"],
        "entry_shard_id": entry_shard_id,
        "entry_mark": gravity_mark_to_record(mark),
        "entry_task": entry_task,
        "gravity_well": gravity_well_to_record(well),
        "created_at_utc": created_at,
        "expires_at_utc": expires_at,
        "ttl_seconds": ttl_seconds,
    }
    wells_dir = Path(out_dir).resolve() / "wells"
    _write_json(wells_dir / f"{well.well_id}.json", record)
    _write_json(Path(out_dir).resolve() / "last_open_well_report.json", record)
    return {
        "schema": OPEN_WELL_SCHEMA,
        "ok": True,
        "field_id": field["field_id"],
        "revision_id": field["revision_id"],
        "entry_shard_id": entry_shard_id,
        "entry_task": entry_task,
        "gravity_well": gravity_well_to_record(well),
        "well_record_path": f"wells/{well.well_id}.json",
        "entry_address": _address_record(mark.address),
        "core_anchor_extraction": False,
        "forbidden_recall_semantics": dict(FORBIDDEN_RECALL_SEMANTICS),
    }


def cleanup_expired_wells(out_dir: Path | str, *, now_utc: str | None = None) -> dict[str, object]:
    now = _parse_utc(now_utc or _utc_now())
    removed: list[str] = []
    wells_dir = Path(out_dir).resolve() / "wells"
    for path in sorted(wells_dir.glob("well_*.json")) if wells_dir.exists() else []:
        record = _read_json(path)
        expires = _parse_utc(str(record.get("expires_at_utc")))
        if expires <= now:
            path.unlink()
            removed.append(path.stem)
    return {"ok": True, "removed_wells": removed, "source_files_mutated": False}


def nollm_surface(
    out_dir: Path | str,
    *,
    well_id: str,
    center_shard_id: str,
    radius: int = 1,
    target_scale: str | int | None = None,
) -> dict[str, object]:
    field, well_record, well = _field_and_well(out_dir, well_id)
    center = _require_shard(field, center_shard_id)
    center_mark = _mark_from_shard(center)
    layer = _target_layer(center_mark.layer, target_scale)
    neighbors = _same_layer_neighbors(field, center_mark, radius=radius)
    coverage = _coverage_candidates(field, center_mark, target_layer=layer) if layer != center_mark.layer else []
    report = {
        "schema": SURFACE_SCHEMA,
        "ok": True,
        "field_id": field["field_id"],
        "revision_id": field["revision_id"],
        "well_id": well.well_id,
        "center_shard_id": center_shard_id,
        "center_address": _address_record(center_mark.address),
        "radius": radius,
        "target_layer": layer,
        "neighbors": neighbors,
        "coverage_candidates": coverage,
        "relationship_methods": sorted({item["relationship_method"] for item in neighbors + coverage}),
        "well_source_snapshot_hash": well_record["source_snapshot_hash"],
        "query_score": None,
        "forbidden_recall_semantics": dict(FORBIDDEN_RECALL_SEMANTICS),
    }
    _write_json(Path(out_dir).resolve() / "last_surface_report.json", report)
    return report


def nollm_focus(out_dir: Path | str, *, well_id: str, target_shard_id: str, target_scale: str | int | None = None) -> dict[str, object]:
    field, _well_record, well = _field_and_well(out_dir, well_id)
    target = _require_shard(field, target_shard_id)
    mark = _mark_from_shard(target)
    requested_layer = _target_layer(mark.layer, target_scale)
    gravity = gravity_report_to_record(create_gravity_report(well, mark))
    coverage = _coverage_candidates(field, mark, target_layer=requested_layer) if requested_layer != mark.layer else []
    report = {
        "schema": FOCUS_SCHEMA,
        "ok": True,
        "field_id": field["field_id"],
        "revision_id": field["revision_id"],
        "well_id": well.well_id,
        "target_shard_id": target_shard_id,
        "target": _public_shard(target),
        "target_scale": target_scale,
        "target_layer": requested_layer,
        "coverage_candidates": coverage,
        "gravity_report": gravity,
        "core_selected_target": False,
        "forbidden_recall_semantics": dict(FORBIDDEN_RECALL_SEMANTICS),
    }
    _write_json(Path(out_dir).resolve() / "last_focus_report.json", report)
    return report


def nollm_drift(out_dir: Path | str, *, well_id: str, current_shard_id: str, chosen_shard_id: str | None = None, radius: int = 1) -> dict[str, object]:
    field, _well_record, well = _field_and_well(out_dir, well_id)
    current = _require_shard(field, current_shard_id)
    current_mark = _mark_from_shard(current)
    neighbors = _same_layer_neighbors(field, current_mark, radius=radius)
    selected = None
    if chosen_shard_id is not None:
        chosen = _require_shard(field, chosen_shard_id)
        selected = _drift_item(well, _mark_from_shard(chosen), chosen, relationship_method=_relationship_method(current_mark, _mark_from_shard(chosen)))
    report = {
        "schema": DRIFT_SCHEMA,
        "ok": True,
        "field_id": field["field_id"],
        "revision_id": field["revision_id"],
        "well_id": well.well_id,
        "current_shard_id": current_shard_id,
        "neighbors": [_drift_item(well, _mark_from_shard(_require_shard(field, str(item["shard_id"]))), _require_shard(field, str(item["shard_id"])), relationship_method=str(item["relationship_method"])) for item in neighbors],
        "selected": selected,
        "return_vector": _return_vector(current_mark, well),
        "drift_is_orientation_only": True,
        "hard_drift_rejection": False,
        "forbidden_recall_semantics": dict(FORBIDDEN_RECALL_SEMANTICS),
    }
    _write_json(Path(out_dir).resolve() / "last_drift_report.json", report)
    return report


def nollm_read(out_dir: Path | str, *, well_id: str, shard_id: str) -> dict[str, object]:
    field, _well_record, _well = _field_and_well(out_dir, well_id)
    shard = _require_shard(field, shard_id)
    report = {
        "schema": READ_SCHEMA,
        "ok": True,
        "field_id": field["field_id"],
        "revision_id": field["revision_id"],
        "well_id": well_id,
        "shard": _public_shard(shard),
        "gravity_mark": gravity_mark_to_record(_mark_from_shard(shard)),
        "read_unit": "dream_shard",
        "raw_source_chunk": False,
        "forbidden_recall_semantics": dict(FORBIDDEN_RECALL_SEMANTICS),
    }
    _write_json(Path(out_dir).resolve() / "last_read_report.json", report)
    return report


def nollm_recall_trace(out_dir: Path | str, *, well_id: str, path: Sequence[str]) -> dict[str, object]:
    field, _well_record, well = _field_and_well(out_dir, well_id)
    items = []
    previous: GravityMark | None = None
    for shard_id in path:
        shard = _require_shard(field, shard_id)
        mark = _mark_from_shard(shard)
        items.append(
            {
                "shard_id": shard_id,
                "address": _address_record(mark.address),
                "relationship_from_previous": _relationship_method(previous, mark) if previous is not None else "entry",
                "gravity_report": gravity_report_to_record(create_gravity_report(well, mark)),
                "return_vector": _return_vector(mark, well),
            }
        )
        previous = mark
    report = {
        "schema": TRACE_SCHEMA,
        "ok": True,
        "field_id": field["field_id"],
        "revision_id": field["revision_id"],
        "well_id": well.well_id,
        "path": list(path),
        "trace": items,
        "prose_digest": None,
        "core_composed_digest": False,
        "forbidden_recall_semantics": dict(FORBIDDEN_RECALL_SEMANTICS),
    }
    _write_json(Path(out_dir).resolve() / "last_recall_trace.json", report)
    return report


def nollm_compose_digest(out_dir: Path | str, *, well_id: str, path: Sequence[str]) -> dict[str, object]:
    return nollm_recall_trace(out_dir, well_id=well_id, path=path)


def run_demo_report(workspace: Path | str, dreamer_output: Path | str, out_dir: Path | str) -> dict[str, object]:
    before = source_snapshot(workspace)
    ingest = dict(ingest_dreamer_fixture(workspace, dreamer_output, out_dir))
    overview = nollm_field_overview(out_dir, workspace=workspace)
    well = nollm_open_well(
        out_dir,
        entry_shard_id="surface-openclaw-nollm",
        entry_task="Cortex-selected OpenClaw/Nollm integration entry",
        anchor_vector={"openclaw": 1.0, "nollm": 1.0, "cortex": 0.7},
        created_at_utc="2026-06-20T00:00:00Z",
    )
    well_id = str(well["gravity_well"]["well_id"])  # type: ignore[index]
    cases = {
        "overview": overview,
        "open_well": well,
        "surface": nollm_surface(out_dir, well_id=well_id, center_shard_id="surface-openclaw-nollm", radius=2, target_scale="bridge"),
        "focus": nollm_focus(out_dir, well_id=well_id, target_shard_id="bridge-active-memory-cortex", target_scale="fine"),
        "drift": nollm_drift(out_dir, well_id=well_id, current_shard_id="bridge-active-memory-cortex", chosen_shard_id="lateral-search-adapter-boundary"),
        "read": nollm_read(out_dir, well_id=well_id, shard_id="fine-no-memory-file-writes"),
        "trace": nollm_recall_trace(out_dir, well_id=well_id, path=["surface-openclaw-nollm", "bridge-active-memory-cortex", "fine-no-memory-file-writes"]),
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
                line_count=len(data.decode("utf-8", errors="replace").splitlines()),
                read_timestamp_utc=datetime.fromtimestamp(stat.st_mtime, timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            )
        )
    return records


def _section_source_text(text: str, *, max_chars: int) -> list[tuple[int, int, str]]:
    lines = text.splitlines()
    if not lines:
        return [(1, 1, "")]
    sections: list[tuple[int, int, str]] = []
    start = 1
    current: list[str] = []
    current_len = 0
    for index, line in enumerate(lines, start=1):
        addition = len(line) + (1 if current else 0)
        if current and current_len + addition > max_chars:
            sections.append((start, index - 1, "\n".join(current)))
            start = index
            current = [line]
            current_len = len(line)
        elif not current and addition > max_chars:
            raise ValueError("single source line exceeds dream packet bound")
        else:
            current.append(line)
            current_len += addition
    if current:
        sections.append((start, start + len(current) - 1, "\n".join(current)))
    return sections


def _prior_field_summary(current_field: Mapping[str, object] | None) -> list[dict[str, object]]:
    summary: list[dict[str, object]] = []
    for shard in _shards(current_field or {}):
        summary.append(
            {
                "semantic_key": shard.get("semantic_key"),
                "text": shard.get("text"),
                "status": shard.get("status"),
                "preferred_scale": shard.get("scale"),
            }
        )
        if len(summary) >= 20:
            break
    return summary


def _validate_dreamer_delta(delta: Mapping[str, object], snapshot: Mapping[str, object], *, dream_packet: Mapping[str, object] | None = None) -> None:
    _assert_no_forbidden_dreamer_fields(delta)
    if delta.get("schema") != DREAMER_CONTRACT_SCHEMA:
        raise ValueError("dreamer delta schema mismatch")
    if delta.get("source_snapshot_hash") != snapshot["source_snapshot_hash"]:
        raise ValueError("dreamer delta source snapshot hash mismatch")
    _required_str(delta, "field_id")
    shards = delta.get("shards")
    if not isinstance(shards, list) or not shards:
        raise ValueError("dreamer delta requires shards")
    seen: set[str] = set()
    file_records = {str(item["source_path"]): item for item in snapshot.get("source_files", []) if isinstance(item, Mapping)}
    hashes = {path: str(item["sha256"]) for path, item in file_records.items()}
    packet_material = _packet_material_index(dream_packet)
    for shard in shards:
        if not isinstance(shard, Mapping):
            raise ValueError("dreamer shard must be a mapping")
        key = _semantic_key(shard)
        if key in seen:
            raise ValueError("duplicate semantic_key")
        seen.add(key)
        if shard.get("status") not in SHARD_STATUSES - {"superseded"}:
            raise ValueError(f"unsupported shard status: {shard.get('status')}")
        if shard.get("preferred_scale") not in SHARD_SCALES:
            raise ValueError(f"unsupported preferred_scale: {shard.get('preferred_scale')}")
        if len(_required_str(shard, "text").strip()) < 8:
            raise ValueError("dream shard text must be independently meaningful")
        anchors = shard.get("anchors")
        if not isinstance(anchors, list) or not anchors or not all(isinstance(item, str) and item.strip() for item in anchors):
            raise ValueError("anchors must be a non-empty list of strings")
        for link in shard.get("source_links", []):
            if not isinstance(link, Mapping):
                raise ValueError("source link must be a mapping")
            path = _required_str(link, "source_path")
            line_range = link.get("line_range")
            if path not in hashes:
                raise ValueError(f"source link points outside snapshot: {path}")
            if link.get("source_sha256") != hashes[path]:
                raise ValueError(f"source hash mismatch for {path}")
            if not isinstance(line_range, list) or len(line_range) != 2 or not all(isinstance(item, int) and item >= 1 for item in line_range) or line_range[0] > line_range[1]:
                raise ValueError("invalid source link line_range")
            line_count = int(file_records[path].get("line_count", 0))
            if line_range[1] > line_count:
                raise ValueError(f"source link line_range exceeds source length for {path}")
            if packet_material is not None and not _line_range_in_packet(packet_material, path, str(link.get("source_sha256")), line_range):
                raise ValueError(f"source link is outside dream packet material for {path}")
    for cluster in delta.get("cluster_intents", []):
        if not isinstance(cluster, Mapping):
            raise ValueError("cluster intent must be a mapping")
        members = cluster.get("members")
        if not isinstance(members, list) or not all(str(item) in seen for item in members):
            raise ValueError("cluster members must reference semantic keys")


def _assert_no_forbidden_dreamer_fields(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key in FORBIDDEN_DREAMER_FIELDS:
                raise ValueError(f"forbidden Dreamer field: {key}")
            _assert_no_forbidden_dreamer_fields(item)
    elif isinstance(value, list):
        for item in value:
            _assert_no_forbidden_dreamer_fields(item)


def _packet_material_index(packet: Mapping[str, object] | None) -> dict[str, list[dict[str, object]]] | None:
    if packet is None:
        return None
    if packet.get("schema") != DREAM_PACKET_SCHEMA:
        raise ValueError("dream packet schema mismatch")
    material = packet.get("source_material")
    if not isinstance(material, list) or not material:
        raise ValueError("dream packet requires source_material")
    result: dict[str, list[dict[str, object]]] = {}
    for item in material:
        if not isinstance(item, Mapping):
            raise ValueError("dream packet material must be mappings")
        source_path = _required_str(item, "source_path")
        _required_str(item, "source_sha256")
        line_range = item.get("line_range")
        if not isinstance(line_range, list) or len(line_range) != 2 or not all(isinstance(value, int) and value >= 1 for value in line_range) or line_range[0] > line_range[1]:
            raise ValueError("dream packet material line_range invalid")
        if not isinstance(item.get("text"), str) or not str(item.get("text")).strip():
            raise ValueError("dream packet material text required")
        result.setdefault(source_path, []).append(dict(item))
    return result


def _line_range_in_packet(packet_index: Mapping[str, Sequence[Mapping[str, object]]], source_path: str, source_sha256: str, line_range: Sequence[int]) -> bool:
    for item in packet_index.get(source_path, []):
        material_range = item.get("line_range")
        if not isinstance(material_range, list) or len(material_range) != 2:
            continue
        if item.get("source_sha256") == source_sha256 and int(material_range[0]) <= int(line_range[0]) and int(line_range[1]) <= int(material_range[1]):
            return True
    return False


def _place_delta(delta: Mapping[str, object], previous: Mapping[str, object] | None) -> list[dict[str, object]]:
    previous_by_key = {
        str(shard.get("semantic_key")): shard
        for shard in _shards(previous or {})
        if shard.get("semantic_key")
    }
    occupied: set[HexAddress] = set()
    placed: list[dict[str, object]] = []
    shards = sorted(delta["shards"], key=lambda item: (SCALE_LAYERS[str(item["preferred_scale"])], str(item["semantic_key"])))  # type: ignore[index]
    for raw in shards:
        if not isinstance(raw, Mapping):
            continue
        key = _semantic_key(raw)
        scale = str(raw["preferred_scale"])
        retained = previous_by_key.get(key)
        if retained is not None:
            address = _mark_from_shard(retained).address
            if address not in occupied:
                placed.append(_placed_shard(raw, address, "retained_address"))
                occupied.add(address)
                continue
        anchor = _placement_anchor(raw, placed)
        address = _nearest_free_address(anchor, SCALE_LAYERS[scale], occupied)
        placed.append(_placed_shard(raw, address, "core_nearest_free_hex"))
        occupied.add(address)
    return sorted(placed, key=lambda item: str(item["shard_id"]))


def _placement_anchor(raw: Mapping[str, object], placed: Sequence[Mapping[str, object]]) -> HexAddress:
    intents = [str(item) for item in raw.get("near_intents", []) if isinstance(item, str)] + [str(item) for item in raw.get("bridge_intents", []) if isinstance(item, str)]
    for intent in intents:
        for shard in placed:
            if shard.get("semantic_key") == intent:
                return _mark_from_shard(shard).address
    return HexAddress(SCALE_LAYERS[str(raw["preferred_scale"])], 0, 0)


def _nearest_free_address(anchor: HexAddress, target_layer: int, occupied: set[HexAddress]) -> HexAddress:
    if anchor.layer != target_layer:
        profile = default_geometry_profile()
        source_layer = layer_spec_from_profile(profile, anchor.layer)
        target_spec = layer_spec_from_profile(profile, target_layer)
        candidates = [item.target for item in coverage_map(anchor, source_layer, target_spec, search_radius=5, min_weight=0.0) if item.source_share > 0.0]
    else:
        candidates = []
    for radius in range(0, 12):
        candidates.extend(HexAddress(target_layer, axial.q, axial.r) for axial in axial_disk(Axial(anchor.q, anchor.r), radius))
        for candidate in sorted(set(candidates), key=lambda item: (abs(item.q - anchor.q) + abs(item.r - anchor.r), item.q, item.r)):
            if candidate not in occupied:
                return candidate
    raise ValueError("unable to place shard in bounded local field")


def _placed_shard(raw: Mapping[str, object], address: HexAddress, method: str) -> dict[str, object]:
    semantic_key = _semantic_key(raw)
    shard = {
        "shard_id": semantic_key,
        "semantic_key": semantic_key,
        "scale": raw["preferred_scale"],
        "text": raw["text"],
        "status": raw["status"],
        "anchors": raw.get("anchors", []),
        "anchor_vector": _anchors_to_vector(raw.get("anchors", [])),
        "source_links": raw.get("source_links", []),
        "source_trace_kind": raw["status"],
        "continuity": raw.get("continuity", {}),
        "dreamer_intents": {
            "near_intents": raw.get("near_intents", []),
            "bridge_intents": raw.get("bridge_intents", []),
        },
        "placement": {
            "chart_id": "chart_openclaw_integration",
            "layer": address.layer,
            "q": address.q,
            "r": address.r,
            "core_placement_method": method,
        },
        "geometry_profile": default_geometry_profile().profile_id,
        "chart_id": "chart_openclaw_integration",
    }
    _validate_anchor_vector(shard["anchor_vector"])  # type: ignore[arg-type]
    return shard


def _dreamer_intents(delta: Mapping[str, object]) -> dict[str, object]:
    return {
        "cluster_intents": delta.get("cluster_intents", []),
        "shard_intents": [
            {
                "semantic_key": item.get("semantic_key"),
                "near_intents": item.get("near_intents", []),
                "bridge_intents": item.get("bridge_intents", []),
                "continuity": item.get("continuity", {}),
            }
            for item in delta.get("shards", [])
            if isinstance(item, Mapping)
        ],
    }


def _publish_revision(out: Path, field: Mapping[str, object], snapshot: Mapping[str, object]) -> None:
    revision_dir = _revision_dir(out, str(field["field_id"]), str(field["revision_id"]))
    tmp_dir = revision_dir.with_name(revision_dir.name + ".tmp")
    if tmp_dir.exists():
        import shutil

        shutil.rmtree(tmp_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    _write_json(tmp_dir / "dream_field.json", field)
    _write_json(tmp_dir / "source_snapshot.json", snapshot)
    _write_json(tmp_dir / "manifest.json", {"field_id": field["field_id"], "revision_id": field["revision_id"], "source_snapshot_hash": field["source_snapshot_hash"]})
    if revision_dir.exists():
        import shutil

        shutil.rmtree(revision_dir)
    tmp_dir.rename(revision_dir)
    current = {"field_id": field["field_id"], "revision_id": field["revision_id"], "path": str(revision_dir.relative_to(out).as_posix())}
    _write_json(out / "current_field.json.tmp", current)
    (out / "current_field.json.tmp").replace(out / "current_field.json")
    _write_json(out / "dream_field.json", field)
    _write_json(out / "source_snapshot.json", snapshot)


def _load_current_field(out: Path) -> dict[str, object] | None:
    pointer = out / "current_field.json"
    if not pointer.exists():
        legacy = out / "dream_field.json"
        return _read_json(legacy) if legacy.exists() else None
    current = _read_json(pointer)
    return _read_json(out / str(current["path"]) / "dream_field.json")


def _load_field_report(out_dir: Path | str) -> dict[str, object]:
    field = _load_current_field(Path(out_dir).resolve())
    if field is None:
        return _error(OVERVIEW_SCHEMA, "field_unavailable", "No current dream field is installed for this workspace. Run an explicit Dreamer ingestion flow.")
    if field.get("schema") != FIELD_SCHEMA:
        return _error(OVERVIEW_SCHEMA, "field_schema_mismatch", "Installed dream field schema is not supported.")
    return field


def _require_field(out_dir: Path | str, *, revision_id: str | None = None, field_id: str | None = None) -> dict[str, object]:
    out = Path(out_dir).resolve()
    if revision_id:
        pointer = _find_revision(out, revision_id, field_id=field_id)
        if pointer is None:
            raise FileNotFoundError(f"field revision unavailable: {revision_id}")
        return _read_json(pointer / "dream_field.json")
    field = _load_field_report(out)
    if field.get("ok") is False:
        raise FileNotFoundError(str(field["message"]))
    return field


def _field_and_well(out_dir: Path | str, well_id: str) -> tuple[dict[str, object], dict[str, object], GravityWell]:
    record = _require_well_record(out_dir, well_id)
    field = _require_field(out_dir, revision_id=str(record["revision_id"]), field_id=str(record["field_id"]))
    well = gravity_well_from_record(record["gravity_well"])  # type: ignore[arg-type]
    return field, record, well


def _require_well_record(out_dir: Path | str, well_id: str) -> dict[str, object]:
    path = Path(out_dir).resolve() / "wells" / f"{well_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"gravity well not found: {well_id}")
    return _read_json(path)


def _find_revision(out: Path, revision_id: str, *, field_id: str | None) -> Path | None:
    if field_id:
        path = _revision_dir(out, field_id, revision_id)
        return path if path.exists() else None
    for path in (out / "fields").glob(f"*/{revision_id}"):
        if path.exists():
            return path
    return None


def _revision_dir(out: Path, field_id: str, revision_id: str) -> Path:
    return out / "fields" / field_id / revision_id


def _shards(field: Mapping[str, object]) -> list[dict[str, object]]:
    return [dict(item) for item in field.get("shards", []) if isinstance(item, Mapping)]


def _require_shard(field: Mapping[str, object], shard_id: str) -> dict[str, object]:
    for shard in _shards(field):
        if shard.get("shard_id") == shard_id:
            return shard
    raise ValueError(f"shard not found in revision {field.get('revision_id')}: {shard_id}")


def _same_layer_neighbors(field: Mapping[str, object], center: GravityMark, *, radius: int) -> list[dict[str, object]]:
    if radius < 0:
        raise ValueError("radius must be non-negative")
    allowed = {HexAddress(center.layer, axial.q, axial.r) for axial in axial_disk(Axial(center.q, center.r), radius)}
    items = []
    for shard in _shards(field):
        mark = _mark_from_shard(shard)
        if mark.content_id == center.content_id or mark.chart_id != center.chart_id or mark.layer != center.layer:
            continue
        if mark.address in allowed:
            items.append({"shard_id": mark.content_id, "address": _address_record(mark.address), "relationship_method": "same_layer_neighbor", "ring_distance": _ring_distance(center, mark)})
    return sorted(items, key=lambda item: (int(item["ring_distance"]), str(item["shard_id"])))


def _coverage_candidates(field: Mapping[str, object], source: GravityMark, *, target_layer: int) -> list[dict[str, object]]:
    profile = default_geometry_profile()
    source_layer = layer_spec_from_profile(profile, source.layer)
    target_layer_spec = layer_spec_from_profile(profile, target_layer)
    coverages = coverage_map(source.address, source_layer, target_layer_spec, search_radius=5, min_weight=0.0)
    coverage_by_target = {item.target: item for item in coverages if item.source_share > 0.0}
    result = []
    for shard in _shards(field):
        mark = _mark_from_shard(shard)
        if mark.chart_id != source.chart_id or mark.layer != target_layer:
            continue
        coverage = coverage_by_target.get(mark.address)
        if coverage is None:
            continue
        result.append({"shard_id": mark.content_id, "address": _address_record(mark.address), "relationship_method": "coverage_template", "source_share": round(coverage.source_share, 12), "target_share": round(coverage.target_share, 12), "jaccard": round(coverage.jaccard, 12)})
    return sorted(result, key=lambda item: (-float(item["source_share"]), str(item["shard_id"])))


def _drift_item(well: GravityWell, mark: GravityMark, shard: Mapping[str, object], *, relationship_method: str) -> dict[str, object]:
    return {"shard_id": mark.content_id, "relationship_method": relationship_method, "shard": _public_shard(shard), "gravity_report": gravity_report_to_record(create_gravity_report(well, mark)), "return_vector": _return_vector(mark, well)}


def _relationship_method(left: GravityMark | None, right: GravityMark) -> str:
    if left is None:
        return "entry"
    if left.chart_id != right.chart_id:
        return "unglued"
    if left.layer == right.layer:
        return "same_layer_neighbor" if _ring_distance(left, right) <= 1 else "same_layer_distant"
    return "coverage_template"


def _return_vector(mark: GravityMark, well: GravityWell) -> dict[str, object]:
    return {"from": _address_record(mark.address), "to": _address_record(well.address), "dq": well.q - mark.q, "dr": well.r - mark.r, "d_layer": well.layer - mark.layer, "method": "axial_delta_to_well"}


def _ring_distance(left: GravityMark, right: GravityMark) -> int:
    if left.layer != right.layer or left.chart_id != right.chart_id:
        return -1
    return max(abs(left.q - right.q), abs(left.r - right.r), abs((-left.q - left.r) - (-right.q - right.r)))


def _mark_from_shard(shard: Mapping[str, object]) -> GravityMark:
    placement = shard["placement"]
    if not isinstance(placement, Mapping):
        raise ValueError("shard placement must be a mapping")
    return GravityMark(
        content_id=str(shard["shard_id"]),
        geometry_profile=str(shard.get("geometry_profile") or default_geometry_profile().profile_id),
        chart_id=str(shard.get("chart_id") or placement.get("chart_id") or "chart_openclaw_integration"),
        layer=int(placement["layer"]),
        q=int(placement["q"]),
        r=int(placement["r"]),
        anchor_vector={str(key): float(value) for key, value in dict(shard.get("anchor_vector", {})).items()},
        provenance=_source_refs(shard),
    )


def _mark_record(shard: Mapping[str, object]) -> dict[str, object]:
    return gravity_mark_to_record(_mark_from_shard(shard))


def _cell_descriptor(shard: Mapping[str, object]) -> dict[str, object]:
    mark = _mark_from_shard(shard)
    return {"shard_id": shard["shard_id"], "semantic_key": shard.get("semantic_key"), "scale": shard["scale"], "text": shard["text"], "status": shard["status"], "address": _address_record(mark.address), "source_trace_kind": shard.get("source_trace_kind", "none")}


def _public_shard(shard: Mapping[str, object]) -> dict[str, object]:
    return {"shard_id": shard["shard_id"], "semantic_key": shard.get("semantic_key"), "scale": shard["scale"], "text": shard["text"], "status": shard["status"], "placement": shard["placement"], "source_links": shard.get("source_links", []), "source_trace_kind": shard.get("source_trace_kind", "none")}


def _scale_availability(shards: Sequence[Mapping[str, object]]) -> dict[str, int]:
    return {scale: sum(1 for item in shards if item.get("scale") == scale) for scale in sorted(SHARD_SCALES)}


def _target_layer(default_layer: int, target_scale: str | int | None) -> int:
    if target_scale is None:
        return default_layer
    if isinstance(target_scale, int):
        if target_scale < 0:
            raise ValueError("target scale layer must be non-negative")
        return target_scale
    if target_scale not in SCALE_LAYERS:
        raise ValueError(f"unsupported target scale: {target_scale}")
    return SCALE_LAYERS[target_scale]


def _address_record(address: HexAddress) -> dict[str, int | str]:
    return {"layer": address.layer, "q": address.q, "r": address.r, "uri": address.uri()}


def _source_refs(shard: Mapping[str, object]) -> str | None:
    links = shard.get("source_links", [])
    if not isinstance(links, list) or not links:
        return None
    refs = []
    for link in links:
        if isinstance(link, Mapping):
            refs.append(f"{link.get('source_path')}:{link.get('line_range')}")
    return ";".join(refs) if refs else None


def _anchors_to_vector(value: object) -> dict[str, float]:
    if not isinstance(value, list) or not value:
        return {"dream": 1.0}
    weights: dict[str, float] = {}
    for item in value:
        key = str(item).strip().lower()
        if key:
            weights[key] = weights.get(key, 0.0) + 1.0
    return weights or {"dream": 1.0}


def _validate_anchor_vector(value: Mapping[str, float]) -> None:
    if not isinstance(value, Mapping) or not value:
        raise ValueError("anchor_vector must be a non-empty mapping")
    for key, item in value.items():
        if not isinstance(key, str) or not key:
            raise ValueError("anchor_vector keys must be non-empty strings")
        if not isinstance(item, (int, float)) or isinstance(item, bool) or item < 0:
            raise ValueError("anchor_vector values must be non-negative numbers")


def _snapshot_hashes(snapshot: Mapping[str, object]) -> dict[str, str]:
    return {str(item["source_path"]): str(item["sha256"]) for item in snapshot.get("source_files", []) if isinstance(item, Mapping)}


def _source_snapshot_hash(snapshot: Mapping[str, object]) -> str:
    stable = [
        {"source_path": item["source_path"], "sha256": item["sha256"], "byte_count": item["byte_count"], "line_count": item.get("line_count", 0)}
        for item in snapshot.get("source_files", [])
        if isinstance(item, Mapping)
    ]
    return _sha256_text(_stable_json(stable))


def _revision_id(field_id: str, snapshot_hash: object, placed: Sequence[Mapping[str, object]], parent: str | None) -> str:
    minimal = [{"semantic_key": item["semantic_key"], "address": item["placement"], "text": item["text"]} for item in placed]
    return f"rev_{_sha256_text(_stable_json({'field_id': field_id, 'snapshot': snapshot_hash, 'parent': parent, 'placed': minimal}))[:16]}"


def _created_at_from_snapshot(snapshot: Mapping[str, object]) -> str:
    stamps = [str(item.get("read_timestamp_utc")) for item in snapshot.get("source_files", []) if isinstance(item, Mapping)]
    return max(stamps) if stamps else "1970-01-01T00:00:00Z"


def _dream_packet_ref(packet: Mapping[str, object] | None) -> dict[str, object] | None:
    if packet is None:
        return None
    material = packet.get("source_material", [])
    return {
        "schema": packet.get("schema"),
        "source_snapshot_hash": packet.get("source_snapshot_hash"),
        "field_id": packet.get("field_id"),
        "material_count": len(material) if isinstance(material, list) else 0,
        "material_ids": [item.get("material_id") for item in material if isinstance(item, Mapping)],
    }


def _semantic_key(record: Mapping[str, object]) -> str:
    key = _required_str(record, "semantic_key")
    return re.sub(r"[^a-zA-Z0-9_.-]+", "-", key.strip()).strip("-").lower()


def _error(schema: str, code: str, message: str) -> dict[str, object]:
    return {"schema": schema, "ok": False, "error": code, "message": message, "forbidden_recall_semantics": dict(FORBIDDEN_RECALL_SEMANTICS)}


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


def _stable_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _add_seconds(value: str, seconds: int) -> str:
    return (_parse_utc(value) + timedelta(seconds=seconds)).replace(microsecond=0).isoformat().replace("+00:00", "Z")


__all__ = [
    "DEMO_SCHEMA",
    "DREAM_PACKET_SCHEMA",
    "DREAMER_CONTRACT_SCHEMA",
    "DRIFT_SCHEMA",
    "FIELD_SCHEMA",
    "FOCUS_SCHEMA",
    "FORBIDDEN_RECALL_SEMANTICS",
    "OPEN_WELL_SCHEMA",
    "OVERVIEW_SCHEMA",
    "READ_SCHEMA",
    "SNAPSHOT_SCHEMA",
    "SURFACE_SCHEMA",
    "TRACE_SCHEMA",
    "cleanup_expired_wells",
    "ingest_dreamer_fixture",
    "nollm_compose_digest",
    "nollm_drift",
    "nollm_field_overview",
    "nollm_focus",
    "nollm_open_well",
    "nollm_read",
    "nollm_recall_trace",
    "nollm_surface",
    "publish_dreamer_delta",
    "build_dream_packet",
    "run_demo_report",
    "source_snapshot",
]
