from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, sqrt
from typing import Literal, Mapping

from nollm.geometry import Axial, HexAddress, axial_distance, coverage_map, world_to_axial, axial_to_world
from nollm.geometry_profiles import get_geometry_profile, layer_spec_from_profile

STATUS = "experimental_internal_only"
ANCHOR_SIMILARITY_METHOD = "cosine_nonnegative_l2"
ProjectionMethod = Literal["coverage_template", "approximate_center", "unavailable"]
DriftClass = Literal[
    "core",
    "halo",
    "near_drift",
    "far_coherent",
    "far_weak",
    "semantic_break",
    "chart_jump",
    "unglued",
]


@dataclass(frozen=True)
class GravityWell:
    well_id: str
    entry_query: str
    geometry_profile: str
    chart_id: str
    layer: int
    q: int
    r: int
    anchor_vector: Mapping[str, float]
    created_at: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty_string(self.well_id, "well_id")
        _require_non_empty_string(self.entry_query, "entry_query")
        _require_non_empty_string(self.geometry_profile, "geometry_profile")
        _require_non_empty_string(self.chart_id, "chart_id")
        _require_non_negative_int(self.layer, "layer")
        _require_int(self.q, "q")
        _require_int(self.r, "r")
        _validate_anchor_vector(self.anchor_vector)
        if self.created_at is not None:
            _require_non_empty_string(self.created_at, "created_at")

    @property
    def address(self) -> HexAddress:
        return HexAddress(self.layer, self.q, self.r)


@dataclass(frozen=True)
class GravityMark:
    content_id: str
    geometry_profile: str
    chart_id: str
    layer: int
    q: int
    r: int
    anchor_vector: Mapping[str, float]
    provenance: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty_string(self.content_id, "content_id")
        _require_non_empty_string(self.geometry_profile, "geometry_profile")
        _require_non_empty_string(self.chart_id, "chart_id")
        _require_non_negative_int(self.layer, "layer")
        _require_int(self.q, "q")
        _require_int(self.r, "r")
        _validate_anchor_vector(self.anchor_vector)
        if self.provenance is not None:
            _require_non_empty_string(self.provenance, "provenance")

    @property
    def address(self) -> HexAddress:
        return HexAddress(self.layer, self.q, self.r)


@dataclass(frozen=True)
class GravityReport:
    well_id: str
    content_id: str
    geometry_profile: str
    well_chart_id: str
    content_chart_id: str
    R_column_ring: int | None
    S_scale_delta: int
    A_anchor_similarity: float
    drift_class: DriftClass
    projection_method: ProjectionMethod
    anchor_similarity_method: str = ANCHOR_SIMILARITY_METHOD
    status: str = STATUS

    def __post_init__(self) -> None:
        _require_non_empty_string(self.well_id, "well_id")
        _require_non_empty_string(self.content_id, "content_id")
        _require_non_empty_string(self.geometry_profile, "geometry_profile")
        _require_non_empty_string(self.well_chart_id, "well_chart_id")
        _require_non_empty_string(self.content_chart_id, "content_chart_id")
        if self.R_column_ring is not None:
            _require_non_negative_int(self.R_column_ring, "R_column_ring")
        _require_non_negative_int(self.S_scale_delta, "S_scale_delta")
        _require_probability(self.A_anchor_similarity, "A_anchor_similarity")
        if self.drift_class not in _ALLOWED_DRIFT_CLASSES:
            raise ValueError("unsupported drift_class")
        if self.projection_method not in ("coverage_template", "approximate_center", "unavailable"):
            raise ValueError("unsupported projection_method")
        if self.anchor_similarity_method != ANCHOR_SIMILARITY_METHOD:
            raise ValueError("anchor_similarity_method must be cosine_nonnegative_l2")
        if self.status != STATUS:
            raise ValueError("gravity report status must be experimental_internal_only")
        if self.R_column_ring is None and self.drift_class not in ("unglued", "chart_jump"):
            raise ValueError("R_column_ring may be null only for unglued or chart_jump reports")


_ALLOWED_DRIFT_CLASSES = {
    "core",
    "halo",
    "near_drift",
    "far_coherent",
    "far_weak",
    "semantic_break",
    "chart_jump",
    "unglued",
}


def anchor_similarity(
    well_anchor_vector: Mapping[str, float],
    mark_anchor_vector: Mapping[str, float],
) -> float:
    _validate_anchor_vector(well_anchor_vector)
    _validate_anchor_vector(mark_anchor_vector)
    keys = set(well_anchor_vector) | set(mark_anchor_vector)
    dot = sum(float(well_anchor_vector.get(key, 0.0)) * float(mark_anchor_vector.get(key, 0.0)) for key in keys)
    well_norm = sqrt(sum(float(value) * float(value) for value in well_anchor_vector.values()))
    mark_norm = sqrt(sum(float(value) * float(value) for value in mark_anchor_vector.values()))
    if well_norm == 0.0 or mark_norm == 0.0:
        return 0.0
    return _clamp_probability(dot / (well_norm * mark_norm))


def create_gravity_report(
    well: GravityWell,
    mark: GravityMark,
    *,
    projection_epsilon: float = 1e-12,
    chart_relation_available: bool = False,
) -> GravityReport:
    if not isinstance(well, GravityWell):
        raise ValueError("well must be a GravityWell")
    if not isinstance(mark, GravityMark):
        raise ValueError("mark must be a GravityMark")
    _require_non_negative_number(projection_epsilon, "projection_epsilon")
    if not isinstance(chart_relation_available, bool):
        raise ValueError("chart_relation_available must be a boolean")

    similarity = anchor_similarity(well.anchor_vector, mark.anchor_vector)
    scale_delta = abs(mark.layer - well.layer)
    projection_method, ring = _project_ring(well, mark, projection_epsilon)
    drift_class = _classify_drift(
        projection_method=projection_method,
        ring=ring,
        similarity=similarity,
        same_chart=well.chart_id == mark.chart_id,
        same_profile=well.geometry_profile == mark.geometry_profile,
        chart_relation_available=chart_relation_available,
    )
    return GravityReport(
        well_id=well.well_id,
        content_id=mark.content_id,
        geometry_profile=mark.geometry_profile,
        well_chart_id=well.chart_id,
        content_chart_id=mark.chart_id,
        R_column_ring=ring,
        S_scale_delta=scale_delta,
        A_anchor_similarity=similarity,
        drift_class=drift_class,
        projection_method=projection_method,
    )


def gravity_well_to_record(well: GravityWell) -> dict[str, object]:
    if not isinstance(well, GravityWell):
        raise ValueError("well must be a GravityWell")
    record: dict[str, object] = {
        "well_id": well.well_id,
        "entry_query": well.entry_query,
        "geometry_profile": well.geometry_profile,
        "chart_id": well.chart_id,
        "layer": well.layer,
        "q": well.q,
        "r": well.r,
        "anchor_vector": dict(sorted((key, float(value)) for key, value in well.anchor_vector.items())),
    }
    if well.created_at is not None:
        record["created_at"] = well.created_at
    return record


def gravity_well_from_record(record: Mapping[str, object]) -> GravityWell:
    if not isinstance(record, Mapping):
        raise ValueError("gravity well record must be a mapping")
    return GravityWell(
        well_id=_record_string(record, "well_id"),
        entry_query=_record_string(record, "entry_query"),
        geometry_profile=_record_string(record, "geometry_profile"),
        chart_id=_record_string(record, "chart_id"),
        layer=_record_int(record, "layer"),
        q=_record_int(record, "q"),
        r=_record_int(record, "r"),
        anchor_vector=_record_anchor_vector(record, "anchor_vector"),
        created_at=_record_optional_string(record, "created_at"),
    )


def gravity_mark_to_record(mark: GravityMark) -> dict[str, object]:
    if not isinstance(mark, GravityMark):
        raise ValueError("mark must be a GravityMark")
    record: dict[str, object] = {
        "content_id": mark.content_id,
        "geometry_profile": mark.geometry_profile,
        "chart_id": mark.chart_id,
        "layer": mark.layer,
        "q": mark.q,
        "r": mark.r,
        "anchor_vector": dict(sorted((key, float(value)) for key, value in mark.anchor_vector.items())),
    }
    if mark.provenance is not None:
        record["provenance"] = mark.provenance
    return record


def gravity_mark_from_record(record: Mapping[str, object]) -> GravityMark:
    if not isinstance(record, Mapping):
        raise ValueError("gravity mark record must be a mapping")
    return GravityMark(
        content_id=_record_string(record, "content_id"),
        geometry_profile=_record_string(record, "geometry_profile"),
        chart_id=_record_string(record, "chart_id"),
        layer=_record_int(record, "layer"),
        q=_record_int(record, "q"),
        r=_record_int(record, "r"),
        anchor_vector=_record_anchor_vector(record, "anchor_vector"),
        provenance=_record_optional_string(record, "provenance"),
    )


def gravity_report_to_record(report: GravityReport) -> dict[str, object]:
    if not isinstance(report, GravityReport):
        raise ValueError("report must be a GravityReport")
    return {
        "well_id": report.well_id,
        "content_id": report.content_id,
        "geometry_profile": report.geometry_profile,
        "well_chart_id": report.well_chart_id,
        "content_chart_id": report.content_chart_id,
        "R_column_ring": report.R_column_ring,
        "S_scale_delta": report.S_scale_delta,
        "A_anchor_similarity": report.A_anchor_similarity,
        "drift_class": report.drift_class,
        "projection_method": report.projection_method,
        "anchor_similarity_method": report.anchor_similarity_method,
        "status": report.status,
    }


def gravity_report_from_record(record: Mapping[str, object]) -> GravityReport:
    if not isinstance(record, Mapping):
        raise ValueError("gravity report record must be a mapping")
    return GravityReport(
        well_id=_record_string(record, "well_id"),
        content_id=_record_string(record, "content_id"),
        geometry_profile=_record_string(record, "geometry_profile"),
        well_chart_id=_record_string(record, "well_chart_id"),
        content_chart_id=_record_string(record, "content_chart_id"),
        R_column_ring=_record_optional_int(record, "R_column_ring"),
        S_scale_delta=_record_int(record, "S_scale_delta"),
        A_anchor_similarity=_record_number(record, "A_anchor_similarity"),
        drift_class=_record_string(record, "drift_class"),  # type: ignore[arg-type]
        projection_method=_record_string(record, "projection_method"),  # type: ignore[arg-type]
        anchor_similarity_method=_record_string(record, "anchor_similarity_method"),
        status=_record_string(record, "status"),
    )


def validate_gravity_report(report: GravityReport | Mapping[str, object]) -> None:
    candidate = gravity_report_from_record(report) if isinstance(report, Mapping) else report
    if not isinstance(candidate, GravityReport):
        raise ValueError("report must be a GravityReport or mapping")
    if not _is_json_primitive(gravity_report_to_record(candidate)):
        raise ValueError("gravity report must be JSON-primitive serializable")


def _project_ring(
    well: GravityWell,
    mark: GravityMark,
    projection_epsilon: float,
) -> tuple[ProjectionMethod, int | None]:
    if well.chart_id != mark.chart_id or well.geometry_profile != mark.geometry_profile:
        return ("unavailable", None)
    mark_axial = Axial(mark.q, mark.r)
    if well.layer == mark.layer:
        return ("coverage_template", axial_distance(Axial(well.q, well.r), mark_axial))

    profile = get_geometry_profile(well.geometry_profile)
    source_layer = layer_spec_from_profile(profile, well.layer)
    target_layer = layer_spec_from_profile(profile, mark.layer)
    search_radius = max(2, int(profile.beta ** abs(mark.layer - well.layer)) + 4)
    try:
        projected = [
            Axial(row.target.q, row.target.r)
            for row in coverage_map(well.address, source_layer, target_layer, search_radius=search_radius)
            if row.source_share > projection_epsilon
        ]
        if projected:
            return ("coverage_template", min(axial_distance(mark_axial, cell) for cell in projected))
    except ValueError:
        pass

    try:
        well_center = axial_to_world(Axial(well.q, well.r), source_layer)
        approximate = world_to_axial(well_center, target_layer)
        return ("approximate_center", axial_distance(mark_axial, approximate))
    except ValueError:
        return ("unavailable", None)


def _classify_drift(
    *,
    projection_method: ProjectionMethod,
    ring: int | None,
    similarity: float,
    same_chart: bool,
    same_profile: bool,
    chart_relation_available: bool,
) -> DriftClass:
    if projection_method == "unavailable" and not (same_chart and same_profile):
        if not same_chart and chart_relation_available:
            return "chart_jump"
        return "unglued"
    if ring is None:
        raise ValueError("R_column_ring is required when projection is not chart_jump or unglued")
    if similarity < 0.4:
        return "semantic_break"
    if ring == 0:
        return "core"
    if ring == 1:
        return "halo"
    if ring in (2, 3) and similarity >= 0.6:
        return "near_drift"
    if ring >= 4 and similarity >= 0.75:
        return "far_coherent"
    return "far_weak"


def _validate_anchor_vector(value: Mapping[str, float]) -> None:
    if not isinstance(value, Mapping):
        raise ValueError("anchor_vector must be a mapping")
    for key, item in value.items():
        if not isinstance(key, str) or not key:
            raise ValueError("anchor_vector keys must be non-empty strings")
        _require_non_negative_number(item, f"anchor_vector[{key}]")


def _record_anchor_vector(record: Mapping[str, object], key: str) -> dict[str, float]:
    value = record.get(key)
    if not isinstance(value, Mapping):
        raise ValueError(f"{key} must be a mapping")
    result = {str(item_key): float(item_value) for item_key, item_value in value.items()}
    _validate_anchor_vector(result)
    return result


def _record_string(record: Mapping[str, object], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _record_optional_string(record: Mapping[str, object], key: str) -> str | None:
    if key not in record or record[key] is None:
        return None
    return _record_string(record, key)


def _record_int(record: Mapping[str, object], key: str) -> int:
    value = record.get(key)
    _require_int(value, key)
    return int(value)


def _record_optional_int(record: Mapping[str, object], key: str) -> int | None:
    if key not in record or record[key] is None:
        return None
    return _record_int(record, key)


def _record_number(record: Mapping[str, object], key: str) -> float:
    value = record.get(key)
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not isfinite(value):
        raise ValueError(f"{key} must be a finite number")
    return float(value)


def _require_non_empty_string(value: object, label: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")


def _require_int(value: object, label: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{label} must be an integer")


def _require_non_negative_int(value: object, label: str) -> None:
    _require_int(value, label)
    if int(value) < 0:
        raise ValueError(f"{label} must be non-negative")


def _require_non_negative_number(value: object, label: str) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not isfinite(value) or value < 0:
        raise ValueError(f"{label} must be a non-negative finite number")


def _require_probability(value: object, label: str) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not isfinite(value) or value < 0 or value > 1:
        raise ValueError(f"{label} must be in [0, 1]")


def _clamp_probability(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


def _is_json_primitive(value: object) -> bool:
    if value is None or isinstance(value, (str, int, float, bool)):
        return True
    if isinstance(value, list):
        return all(_is_json_primitive(item) for item in value)
    if isinstance(value, Mapping):
        return all(isinstance(key, str) and _is_json_primitive(item) for key, item in value.items())
    return False


__all__ = [
    "ANCHOR_SIMILARITY_METHOD",
    "GravityMark",
    "GravityReport",
    "GravityWell",
    "STATUS",
    "anchor_similarity",
    "create_gravity_report",
    "gravity_mark_from_record",
    "gravity_mark_to_record",
    "gravity_report_from_record",
    "gravity_report_to_record",
    "gravity_well_from_record",
    "gravity_well_to_record",
    "validate_gravity_report",
]
