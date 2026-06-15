from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from nollm.chart_gluing import LocalChartSpec
from nollm.geometry import Axial, HexAddress, axial_disk

ALLOWED_PLACEMENT_STATUSES = frozenset(
    {
        "candidate",
        "placed_uncertain",
        "new_chart_candidate",
        "rejected",
    }
)


@dataclass(frozen=True)
class PlacementEnergy:
    semantic_hint_cost: float = 0.0
    geometric_distance_cost: float = 0.0
    density_pressure_cost: float = 0.0
    coverage_potential_cost: float = 0.0
    future_scan_cost: float = 0.0
    merge_complexity_cost: float = 0.0
    compute_cost: float = 0.0

    def __post_init__(self) -> None:
        validate_placement_energy(self)

    @property
    def total(self) -> float:
        return float(
            self.semantic_hint_cost
            + self.geometric_distance_cost
            + self.density_pressure_cost
            + self.coverage_potential_cost
            + self.future_scan_cost
            + self.merge_complexity_cost
            + self.compute_cost
        )


@dataclass(frozen=True)
class DreamPlacementCandidate:
    shard_id: str
    chart_id: str
    address: HexAddress
    energy: PlacementEnergy
    anchors_used: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()
    status: str = "candidate"

    def __post_init__(self) -> None:
        object.__setattr__(self, "anchors_used", tuple(self.anchors_used))
        object.__setattr__(self, "reasons", tuple(self.reasons))
        validate_dream_placement_candidate(self)


def validate_placement_energy(energy: PlacementEnergy) -> None:
    if not isinstance(energy, PlacementEnergy):
        raise ValueError("energy must be a PlacementEnergy")
    for field_name in _ENERGY_FIELDS:
        value = getattr(energy, field_name)
        _require_non_negative_number(value, field_name)


def validate_dream_placement_candidate(candidate: DreamPlacementCandidate) -> None:
    if not isinstance(candidate, DreamPlacementCandidate):
        raise ValueError("candidate must be a DreamPlacementCandidate")
    _require_non_empty_string(candidate.shard_id, "shard_id")
    _require_non_empty_string(candidate.chart_id, "chart_id")
    if not isinstance(candidate.address, HexAddress):
        raise ValueError("address must be a HexAddress")
    if not isinstance(candidate.energy, PlacementEnergy):
        raise ValueError("energy must be a PlacementEnergy")
    if candidate.status not in ALLOWED_PLACEMENT_STATUSES:
        raise ValueError(f"unsupported placement status: {candidate.status}")
    _require_string_tuple(candidate.anchors_used, "anchors_used", allow_empty_items=False)
    _require_string_tuple(candidate.reasons, "reasons", allow_empty_items=False)


def rank_placement_candidates(
    candidates: Iterable[DreamPlacementCandidate],
) -> list[DreamPlacementCandidate]:
    items = list(candidates)
    for item in items:
        validate_dream_placement_candidate(item)
    return sorted(
        items,
        key=lambda candidate: (
            candidate.energy.total,
            candidate.address.layer,
            candidate.address.q,
            candidate.address.r,
            candidate.chart_id,
            candidate.shard_id,
        ),
    )


def placement_candidate_to_record(candidate: DreamPlacementCandidate) -> dict[str, object]:
    validate_dream_placement_candidate(candidate)
    return {
        "shard_id": candidate.shard_id,
        "chart_id": candidate.chart_id,
        "address": {
            "layer": candidate.address.layer,
            "q": candidate.address.q,
            "r": candidate.address.r,
        },
        "energy": {field_name: getattr(candidate.energy, field_name) for field_name in _ENERGY_FIELDS},
        "anchors_used": list(candidate.anchors_used),
        "reasons": list(candidate.reasons),
        "status": candidate.status,
    }


def placement_candidate_from_record(record: Mapping[str, object]) -> DreamPlacementCandidate:
    if not isinstance(record, Mapping):
        raise ValueError("record must be a mapping")
    address_record = record.get("address")
    energy_record = record.get("energy")
    anchors_used = record.get("anchors_used", ())
    reasons = record.get("reasons", ())
    if not isinstance(address_record, Mapping):
        raise ValueError("address must be a mapping")
    if not isinstance(energy_record, Mapping):
        raise ValueError("energy must be a mapping")
    if not isinstance(anchors_used, (list, tuple)):
        raise ValueError("anchors_used must be a list or tuple")
    if not isinstance(reasons, (list, tuple)):
        raise ValueError("reasons must be a list or tuple")

    energy_values = {
        field_name: _record_number(energy_record, field_name, default=0.0)
        for field_name in _ENERGY_FIELDS
    }
    return DreamPlacementCandidate(
        shard_id=_record_string(record, "shard_id"),
        chart_id=_record_string(record, "chart_id"),
        address=HexAddress(
            layer=_record_int(address_record, "layer"),
            q=_record_int(address_record, "q"),
            r=_record_int(address_record, "r"),
        ),
        energy=PlacementEnergy(**energy_values),
        anchors_used=tuple(anchors_used),
        reasons=tuple(reasons),
        status=_record_string(record, "status", default="candidate"),
    )


def candidate_addresses_for_chart(
    chart: LocalChartSpec,
    layer: int | None = None,
    radius: int | None = None,
) -> list[HexAddress]:
    if not isinstance(chart, LocalChartSpec):
        raise ValueError("chart must be a LocalChartSpec")
    target_layer = chart.seed.layer if layer is None else layer
    target_radius = chart.source_radius if radius is None else radius
    _require_non_negative_int(target_layer, "layer")
    _require_non_negative_int(target_radius, "radius")
    center = Axial(chart.seed.q, chart.seed.r)
    return [
        HexAddress(target_layer, axial.q, axial.r)
        for axial in axial_disk(center, target_radius)
    ]


def _require_non_empty_string(value: str, label: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")


def _require_string_tuple(value: tuple[str, ...], label: str, allow_empty_items: bool) -> None:
    if not isinstance(value, tuple):
        raise ValueError(f"{label} must be a tuple")
    for item in value:
        if not isinstance(item, str) or (not allow_empty_items and not item):
            raise ValueError(f"{label} must contain non-empty strings")


def _require_non_negative_number(value: float, label: str) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{label} must be a non-negative number")


def _require_non_negative_int(value: int, label: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")


def _record_string(record: Mapping[str, object], key: str, default: str | None = None) -> str:
    value = record.get(key, default)
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return value


def _record_int(record: Mapping[str, object], key: str) -> int:
    value = record.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{key} must be an integer")
    return value


def _record_number(record: Mapping[str, object], key: str, default: float) -> float:
    value = record.get(key, default)
    _require_non_negative_number(value, key)
    return float(value)


_ENERGY_FIELDS = (
    "semantic_hint_cost",
    "geometric_distance_cost",
    "density_pressure_cost",
    "coverage_potential_cost",
    "future_scan_cost",
    "merge_complexity_cost",
    "compute_cost",
)


__all__ = [
    "ALLOWED_PLACEMENT_STATUSES",
    "PlacementEnergy",
    "DreamPlacementCandidate",
    "validate_placement_energy",
    "validate_dream_placement_candidate",
    "rank_placement_candidates",
    "placement_candidate_to_record",
    "placement_candidate_from_record",
    "candidate_addresses_for_chart",
]
