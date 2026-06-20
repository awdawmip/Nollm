from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
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


FIELD_SCHEMA = "nollm.dream_cortex_field.v2"
SNAPSHOT_SCHEMA = "nollm.source_snapshot.v1"
DREAMER_CONTRACT_SCHEMA = "nollm.dreamer_contract_fixture.v1"
OVERVIEW_SCHEMA = "nollm.cortex.field_overview.v1"
OPEN_WELL_SCHEMA = "nollm.cortex.open_well.v1"
SURFACE_SCHEMA = "nollm.cortex.surface_geometry.v2"
FOCUS_SCHEMA = "nollm.cortex.focus_geometry.v2"
DRIFT_SCHEMA = "nollm.cortex.drift_geometry.v2"
READ_SCHEMA = "nollm.cortex.read.v2"
TRACE_SCHEMA = "nollm.cortex.recall_trace.v1"
DEMO_SCHEMA = "nollm.dream_cortex_demo_report.v2"

SOURCE_GLOBS = ("MEMORY.md", "DREAMS.md", "memory/*.md")
SHARD_STATUSES = {"source_backed", "derived", "tentative", "superseded"}
SHARD_SCALES = {"coarse", "bridge", "fine"}
SCALE_LAYERS = {"coarse": 0, "bridge": 1, "fine": 2}
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
    profile = default_geometry_profile()
    geometry_profile = str(dream.get("geometry_profile") or profile.profile_id)
    chart_id = str(dream.get("chart_id") or "chart_openclaw_integration")
    shards = [_normalize_shard(item, geometry_profile=geometry_profile, chart_id=chart_id) for item in dream["shards"]]  # type: ignore[index]
    marks = [_mark_record(shard) for shard in shards]
    field = {
        "schema": FIELD_SCHEMA,
        "field_id": str(dream.get("field_id")),
        "geometry_profile": geometry_profile,
        "chart_id": chart_id,
        "source_snapshot": snapshot,
        "dreamer_output_path": str(output_path),
        "charts": dream.get("charts", []),
        "shards": sorted(shards, key=lambda item: str(item["shard_id"])),
        "gravity_marks": sorted(marks, key=lambda item: str(item["content_id"])),
        "dreamer_relation_proposals": sorted(
            dream.get("relations", []),
            key=lambda item: (str(item.get("from")), str(item.get("to"))) if isinstance(item, Mapping) else ("", ""),
        ),
        "projection": {
            "method": "explicit_fixture_dreamer_projection",
            "llm_provider_call": False,
            "source_files_mutated": False,
            "recall_unit": "dream_shard",
            "raw_markdown_chunks_are_recall_units": False,
            "runtime_selection": "cortex_explicit_geometry_path",
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
        "gravity_mark_count": len(field["gravity_marks"]),
        "source_files_mutated": False,
        "forbidden_recall_semantics": dict(FORBIDDEN_RECALL_SEMANTICS),
    }
    _write_json(out / "ingest_report.json", report)
    return report


def nollm_field_overview(out_dir: Path | str, *, field_id: str | None = None, limit: int = 20) -> dict[str, object]:
    field = _load_field_report(out_dir)
    if field.get("ok") is False:
        return field
    if field_id is not None and field.get("field_id") != field_id:
        return _error(OVERVIEW_SCHEMA, "field_not_found", f"Field is not installed: {field_id}")
    shards = _shards(field)
    coarse = [item for item in shards if item.get("scale") == "coarse"]
    report = {
        "schema": OVERVIEW_SCHEMA,
        "ok": True,
        "field_id": field["field_id"],
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
) -> dict[str, object]:
    field = _require_field(out_dir)
    _validate_anchor_vector(anchor_vector)
    entry = _require_shard(field, entry_shard_id)
    mark = _mark_from_shard(entry)
    well = GravityWell(
        well_id=f"well_{_sha256_text(field['field_id'] + ':' + entry_shard_id + ':' + entry_task + ':' + _stable_json(anchor_vector))[:16]}",
        entry_query=entry_task,
        geometry_profile=mark.geometry_profile,
        chart_id=mark.chart_id,
        layer=mark.layer,
        q=mark.q,
        r=mark.r,
        anchor_vector=dict(anchor_vector),
        created_at=None,
    )
    record = gravity_well_to_record(well)
    _write_json(Path(out_dir).resolve() / "last_gravity_well.json", record)
    report = {
        "schema": OPEN_WELL_SCHEMA,
        "ok": True,
        "field_id": field["field_id"],
        "entry_shard_id": entry_shard_id,
        "entry_task": entry_task,
        "gravity_well": record,
        "entry_address": _address_record(mark.address),
        "core_anchor_extraction": False,
        "forbidden_recall_semantics": dict(FORBIDDEN_RECALL_SEMANTICS),
    }
    _write_json(Path(out_dir).resolve() / "last_open_well_report.json", report)
    return report


def nollm_surface(
    out_dir: Path | str,
    *,
    well_id: str,
    center_shard_id: str,
    radius: int = 1,
    target_scale: str | int | None = None,
) -> dict[str, object]:
    field = _require_field(out_dir)
    well = _require_well(out_dir, well_id)
    center = _require_shard(field, center_shard_id)
    center_mark = _mark_from_shard(center)
    layer = _target_layer(center_mark.layer, target_scale)
    neighbors = _same_layer_neighbors(field, center_mark, radius=radius)
    coverage = _coverage_candidates(field, center_mark, target_layer=layer) if layer != center_mark.layer else []
    report = {
        "schema": SURFACE_SCHEMA,
        "ok": True,
        "field_id": field["field_id"],
        "well_id": well.well_id,
        "center_shard_id": center_shard_id,
        "center_address": _address_record(center_mark.address),
        "radius": radius,
        "target_layer": layer,
        "neighbors": neighbors,
        "coverage_candidates": coverage,
        "relationship_methods": sorted({item["relationship_method"] for item in neighbors + coverage}),
        "query_score": None,
        "forbidden_recall_semantics": dict(FORBIDDEN_RECALL_SEMANTICS),
    }
    _write_json(Path(out_dir).resolve() / "last_surface_report.json", report)
    return report


def nollm_focus(
    out_dir: Path | str,
    *,
    well_id: str,
    target_shard_id: str,
    target_scale: str | int | None = None,
) -> dict[str, object]:
    field = _require_field(out_dir)
    well = _require_well(out_dir, well_id)
    target = _require_shard(field, target_shard_id)
    mark = _mark_from_shard(target)
    requested_layer = _target_layer(mark.layer, target_scale)
    gravity = gravity_report_to_record(create_gravity_report(well, mark))
    coverage = _coverage_candidates(field, mark, target_layer=requested_layer) if requested_layer != mark.layer else []
    report = {
        "schema": FOCUS_SCHEMA,
        "ok": True,
        "field_id": field["field_id"],
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


def nollm_drift(
    out_dir: Path | str,
    *,
    well_id: str,
    current_shard_id: str,
    chosen_shard_id: str | None = None,
    radius: int = 1,
) -> dict[str, object]:
    field = _require_field(out_dir)
    well = _require_well(out_dir, well_id)
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


def nollm_read(out_dir: Path | str, *, shard_id: str) -> dict[str, object]:
    field = _require_field(out_dir)
    shard = _require_shard(field, shard_id)
    report = {
        "schema": READ_SCHEMA,
        "ok": True,
        "field_id": field["field_id"],
        "shard": _public_shard(shard),
        "gravity_mark": gravity_mark_to_record(_mark_from_shard(shard)),
        "read_unit": "dream_shard",
        "raw_source_chunk": False,
        "forbidden_recall_semantics": dict(FORBIDDEN_RECALL_SEMANTICS),
    }
    _write_json(Path(out_dir).resolve() / "last_read_report.json", report)
    return report


def nollm_recall_trace(out_dir: Path | str, *, well_id: str, path: Sequence[str]) -> dict[str, object]:
    field = _require_field(out_dir)
    well = _require_well(out_dir, well_id)
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
    ingest.pop("out_dir", None)
    overview = nollm_field_overview(out_dir)
    well = nollm_open_well(
        out_dir,
        entry_shard_id="surface_openclaw_nollm",
        entry_task="Cortex-selected OpenClaw/Nollm integration entry",
        anchor_vector={"openclaw": 1.0, "nollm": 1.0, "cortex": 0.7},
    )
    well_id = str(well["gravity_well"]["well_id"])  # type: ignore[index]
    cases = {
        "overview": overview,
        "open_well": well,
        "surface": nollm_surface(out_dir, well_id=well_id, center_shard_id="surface_openclaw_nollm", radius=2, target_scale="bridge"),
        "focus": nollm_focus(out_dir, well_id=well_id, target_shard_id="bridge_active_memory_cortex", target_scale="fine"),
        "drift": nollm_drift(out_dir, well_id=well_id, current_shard_id="bridge_active_memory_cortex", chosen_shard_id="lateral_search_adapter_boundary"),
        "read": nollm_read(out_dir, shard_id="fine_no_memory_file_writes"),
        "trace": nollm_recall_trace(out_dir, well_id=well_id, path=["surface_openclaw_nollm", "bridge_active_memory_cortex", "fine_no_memory_file_writes"]),
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
        _address_from_placement(placement, str(shard["scale"]))


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


def _load_field_report(out_dir: Path | str) -> dict[str, object]:
    path = Path(out_dir).resolve() / "dream_field.json"
    if not path.exists():
        return _error(
            OVERVIEW_SCHEMA,
            "field_unavailable",
            "No current dream field is installed for this workspace. Run an explicit Dreamer ingestion flow.",
        )
    field = _read_json(path)
    if field.get("schema") != FIELD_SCHEMA:
        return _error(OVERVIEW_SCHEMA, "field_schema_mismatch", "Installed dream field schema is not supported.")
    return field


def _require_field(out_dir: Path | str) -> dict[str, object]:
    field = _load_field_report(out_dir)
    if field.get("ok") is False:
        raise FileNotFoundError(str(field["message"]))
    return field


def _require_well(out_dir: Path | str, well_id: str) -> GravityWell:
    path = Path(out_dir).resolve() / "last_gravity_well.json"
    if not path.exists():
        raise FileNotFoundError("gravity well is missing; Cortex must call nollm_open_well first")
    well = gravity_well_from_record(_read_json(path))
    if well.well_id != well_id:
        raise ValueError(f"gravity well not found: {well_id}")
    return well


def _shards(field: Mapping[str, object]) -> list[dict[str, object]]:
    return [dict(item) for item in field.get("shards", []) if isinstance(item, Mapping)]


def _require_shard(field: Mapping[str, object], shard_id: str) -> dict[str, object]:
    for shard in _shards(field):
        if shard.get("shard_id") == shard_id:
            return shard
    raise ValueError(f"shard not found: {shard_id}")


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
            items.append(
                {
                    "shard_id": mark.content_id,
                    "address": _address_record(mark.address),
                    "relationship_method": "same_layer_neighbor",
                    "ring_distance": _ring_distance(center, mark),
                }
            )
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
        result.append(
            {
                "shard_id": mark.content_id,
                "address": _address_record(mark.address),
                "relationship_method": "coverage_template",
                "source_share": round(coverage.source_share, 12),
                "target_share": round(coverage.target_share, 12),
                "jaccard": round(coverage.jaccard, 12),
            }
        )
    return sorted(result, key=lambda item: (-float(item["source_share"]), str(item["shard_id"])))


def _drift_item(well: GravityWell, mark: GravityMark, shard: Mapping[str, object], *, relationship_method: str) -> dict[str, object]:
    return {
        "shard_id": mark.content_id,
        "relationship_method": relationship_method,
        "shard": _public_shard(shard),
        "gravity_report": gravity_report_to_record(create_gravity_report(well, mark)),
        "return_vector": _return_vector(mark, well),
    }


def _relationship_method(left: GravityMark | None, right: GravityMark) -> str:
    if left is None:
        return "entry"
    if left.chart_id != right.chart_id:
        return "unglued"
    if left.layer == right.layer:
        return "same_layer_neighbor" if _ring_distance(left, right) <= 1 else "same_layer_distant"
    return "coverage_template"


def _return_vector(mark: GravityMark, well: GravityWell) -> dict[str, object]:
    return {
        "from": _address_record(mark.address),
        "to": _address_record(well.address),
        "dq": well.q - mark.q,
        "dr": well.r - mark.r,
        "d_layer": well.layer - mark.layer,
        "method": "axial_delta_to_well",
    }


def _ring_distance(left: GravityMark, right: GravityMark) -> int:
    if left.layer != right.layer or left.chart_id != right.chart_id:
        return -1
    return max(abs(left.q - right.q), abs(left.r - right.r), abs((-left.q - left.r) - (-right.q - right.r)))


def _normalize_shard(record: Mapping[str, object], *, geometry_profile: str, chart_id: str) -> dict[str, object]:
    shard = dict(record)
    placement = dict(shard["placement"]) if isinstance(shard.get("placement"), Mapping) else {}
    address = _address_from_placement(placement, str(shard["scale"]))
    placement.update({"chart_id": chart_id, "layer": address.layer, "q": address.q, "r": address.r})
    shard["placement"] = placement
    shard["geometry_profile"] = geometry_profile
    shard["chart_id"] = chart_id
    if "anchor_vector" not in shard:
        shard["anchor_vector"] = _anchors_to_vector(shard.get("anchors", []))
    _validate_anchor_vector(shard["anchor_vector"])  # type: ignore[arg-type]
    return shard


def _address_from_placement(placement: Mapping[str, object], scale: str) -> HexAddress:
    layer = int(placement.get("layer", SCALE_LAYERS.get(scale, 0)))
    q = int(placement.get("q", 0))
    r = int(placement.get("r", 0))
    return HexAddress(layer, q, r)


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
    return {
        "shard_id": shard["shard_id"],
        "scale": shard["scale"],
        "text": shard["text"],
        "status": shard["status"],
        "address": _address_record(mark.address),
        "source_trace_kind": shard.get("source_trace_kind", "none"),
    }


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
    return {
        str(item["source_path"]): str(item["sha256"])
        for item in snapshot.get("source_files", [])
        if isinstance(item, Mapping)
    }


def _error(schema: str, code: str, message: str) -> dict[str, object]:
    return {
        "schema": schema,
        "ok": False,
        "error": code,
        "message": message,
        "forbidden_recall_semantics": dict(FORBIDDEN_RECALL_SEMANTICS),
    }


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


def _stable_json(value: Mapping[str, float]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


__all__ = [
    "DEMO_SCHEMA",
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
    "ingest_dreamer_fixture",
    "nollm_compose_digest",
    "nollm_drift",
    "nollm_field_overview",
    "nollm_focus",
    "nollm_open_well",
    "nollm_read",
    "nollm_recall_trace",
    "nollm_surface",
    "run_demo_report",
    "source_snapshot",
]
