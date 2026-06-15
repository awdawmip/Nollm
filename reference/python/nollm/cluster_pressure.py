from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from nollm.dream_placement import DreamPlacementCandidate
from nollm.geometry import HexAddress, axial_distance

ALLOWED_COARSE_EMERGENCE_STATUSES = frozenset({"candidate", "rejected", "archived"})


@dataclass(frozen=True)
class ClusterPressureSample:
    chart_id: str
    address: HexAddress
    placement_count: int
    pressure: float
    reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_non_empty_string(self.chart_id, "chart_id")
        if not isinstance(self.address, HexAddress):
            raise ValueError("address must be a HexAddress")
        _require_non_negative_int(self.placement_count, "placement_count")
        _require_non_negative_number(self.pressure, "pressure")
        object.__setattr__(self, "reasons", tuple(self.reasons))
        _require_string_tuple(self.reasons, "reasons")


@dataclass(frozen=True)
class CoarseEmergenceCandidate:
    chart_id: str
    center: HexAddress
    radius: int
    pressure_sum: float
    sample_count: int
    status: str = "candidate"

    def __post_init__(self) -> None:
        _require_non_empty_string(self.chart_id, "chart_id")
        if not isinstance(self.center, HexAddress):
            raise ValueError("center must be a HexAddress")
        _require_non_negative_int(self.radius, "radius")
        _require_non_negative_number(self.pressure_sum, "pressure_sum")
        _require_non_negative_int(self.sample_count, "sample_count")
        if self.status not in ALLOWED_COARSE_EMERGENCE_STATUSES:
            raise ValueError(f"unsupported coarse emergence status: {self.status}")


def summarize_pressure(
    candidates: Iterable[DreamPlacementCandidate],
    chart_id: str,
    radius: int = 0,
) -> tuple[ClusterPressureSample, ...]:
    _require_non_empty_string(chart_id, "chart_id")
    _require_non_negative_int(radius, "radius")
    grouped: dict[HexAddress, list[DreamPlacementCandidate]] = {}
    for candidate in candidates:
        if not isinstance(candidate, DreamPlacementCandidate):
            raise ValueError("candidates must contain DreamPlacementCandidate instances")
        if candidate.chart_id != chart_id:
            continue
        grouped.setdefault(candidate.address, []).append(candidate)
    samples = []
    for address, items in grouped.items():
        reasons = tuple(reason for item in items for reason in item.reasons)
        samples.append(
            ClusterPressureSample(
                chart_id=chart_id,
                address=address,
                placement_count=len(items),
                pressure=float(sum(1.0 / (1.0 + item.energy.total) for item in items)),
                reasons=reasons or (f"radius={radius}",),
            )
        )
    return tuple(rank_pressure_samples(samples))


def rank_pressure_samples(samples: Iterable[ClusterPressureSample]) -> list[ClusterPressureSample]:
    items = list(samples)
    for item in items:
        if not isinstance(item, ClusterPressureSample):
            raise ValueError("samples must contain ClusterPressureSample instances")
    return sorted(
        items,
        key=lambda sample: (
            -sample.pressure,
            -sample.placement_count,
            sample.address.layer,
            sample.address.q,
            sample.address.r,
            sample.chart_id,
        ),
    )


def propose_coarse_emergence(
    samples: Iterable[ClusterPressureSample],
    chart_id: str,
    center: HexAddress,
    radius: int,
) -> CoarseEmergenceCandidate:
    _require_non_empty_string(chart_id, "chart_id")
    if not isinstance(center, HexAddress):
        raise ValueError("center must be a HexAddress")
    _require_non_negative_int(radius, "radius")
    included = [
        sample
        for sample in samples
        if sample.chart_id == chart_id
        and sample.address.layer == center.layer
        and axial_distance(sample.address.axial, center.axial) <= radius
    ]
    return CoarseEmergenceCandidate(
        chart_id=chart_id,
        center=center,
        radius=radius,
        pressure_sum=sum(sample.pressure for sample in included),
        sample_count=len(included),
    )


def pressure_sample_to_record(sample: ClusterPressureSample) -> dict[str, object]:
    if not isinstance(sample, ClusterPressureSample):
        raise ValueError("sample must be a ClusterPressureSample")
    return {
        "chart_id": sample.chart_id,
        "address": _address_to_record(sample.address),
        "placement_count": sample.placement_count,
        "pressure": sample.pressure,
        "reasons": list(sample.reasons),
    }


def pressure_sample_from_record(record: Mapping[str, object]) -> ClusterPressureSample:
    if not isinstance(record, Mapping):
        raise ValueError("record must be a mapping")
    reasons = record.get("reasons", ())
    if not isinstance(reasons, (list, tuple)):
        raise ValueError("reasons must be a list or tuple")
    return ClusterPressureSample(
        chart_id=_record_string(record, "chart_id"),
        address=_address_from_record(record.get("address")),
        placement_count=_record_int(record, "placement_count"),
        pressure=_record_number(record, "pressure"),
        reasons=tuple(reasons),
    )


def coarse_emergence_to_record(candidate: CoarseEmergenceCandidate) -> dict[str, object]:
    if not isinstance(candidate, CoarseEmergenceCandidate):
        raise ValueError("candidate must be a CoarseEmergenceCandidate")
    return {
        "chart_id": candidate.chart_id,
        "center": _address_to_record(candidate.center),
        "radius": candidate.radius,
        "pressure_sum": candidate.pressure_sum,
        "sample_count": candidate.sample_count,
        "status": candidate.status,
    }


def coarse_emergence_from_record(record: Mapping[str, object]) -> CoarseEmergenceCandidate:
    if not isinstance(record, Mapping):
        raise ValueError("record must be a mapping")
    return CoarseEmergenceCandidate(
        chart_id=_record_string(record, "chart_id"),
        center=_address_from_record(record.get("center")),
        radius=_record_int(record, "radius"),
        pressure_sum=_record_number(record, "pressure_sum"),
        sample_count=_record_int(record, "sample_count"),
        status=_record_string(record, "status", "candidate"),
    )


def _address_to_record(address: HexAddress) -> dict[str, int]:
    return {"layer": address.layer, "q": address.q, "r": address.r}


def _address_from_record(record: object) -> HexAddress:
    if not isinstance(record, Mapping):
        raise ValueError("address must be a mapping")
    return HexAddress(
        _record_non_negative_int(record, "layer"),
        _record_int(record, "q"),
        _record_int(record, "r"),
    )


def _require_non_empty_string(value: str, label: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")


def _require_non_negative_int(value: int, label: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")


def _require_non_negative_number(value: float, label: str) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{label} must be a non-negative number")


def _require_string_tuple(value: tuple[str, ...], label: str) -> None:
    if not isinstance(value, tuple):
        raise ValueError(f"{label} must be a tuple")
    for item in value:
        _require_non_empty_string(item, label)


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


def _record_non_negative_int(record: Mapping[str, object], key: str) -> int:
    value = _record_int(record, key)
    _require_non_negative_int(value, key)
    return value


def _record_number(record: Mapping[str, object], key: str) -> float:
    value = record.get(key)
    _require_non_negative_number(value, key)  # type: ignore[arg-type]
    return float(value)


__all__ = [
    "ALLOWED_COARSE_EMERGENCE_STATUSES",
    "ClusterPressureSample",
    "CoarseEmergenceCandidate",
    "summarize_pressure",
    "rank_pressure_samples",
    "propose_coarse_emergence",
    "pressure_sample_to_record",
    "pressure_sample_from_record",
    "coarse_emergence_to_record",
    "coarse_emergence_from_record",
]
