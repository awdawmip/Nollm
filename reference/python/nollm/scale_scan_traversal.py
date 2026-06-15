from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from nollm.geometry import Axial, HexAddress, axial_disk

ALLOWED_SCALE_SCAN_STATUSES = frozenset({"candidate", "rejected", "archived"})


@dataclass(frozen=True)
class ScaleScanStep:
    layer: int
    chart_id: str
    addresses: tuple[HexAddress, ...]
    reason: str

    def __post_init__(self) -> None:
        _require_non_negative_int(self.layer, "layer")
        _require_non_empty_string(self.chart_id, "chart_id")
        object.__setattr__(self, "addresses", tuple(self.addresses))
        if not self.addresses:
            raise ValueError("addresses must be non-empty")
        for address in self.addresses:
            if not isinstance(address, HexAddress):
                raise ValueError("addresses must contain HexAddress instances")
            if address.layer != self.layer:
                raise ValueError("step address layer must match step layer")
        _require_non_empty_string(self.reason, "reason")


@dataclass(frozen=True)
class ScaleScanPlan:
    plan_id: str
    shard_id: str
    steps: tuple[ScaleScanStep, ...]
    stop_reason: str
    status: str = "candidate"

    def __post_init__(self) -> None:
        _require_non_empty_string(self.plan_id, "plan_id")
        _require_non_empty_string(self.shard_id, "shard_id")
        object.__setattr__(self, "steps", tuple(self.steps))
        if not self.steps:
            raise ValueError("steps must be non-empty")
        for step in self.steps:
            validate_scale_scan_step(step)
        _require_non_empty_string(self.stop_reason, "stop_reason")
        if self.status not in ALLOWED_SCALE_SCAN_STATUSES:
            raise ValueError(f"unsupported scale scan status: {self.status}")


def make_linear_scale_scan_plan(
    shard_id: str,
    chart_id: str,
    start_address: HexAddress,
    max_layers: int,
    radius: int,
) -> ScaleScanPlan:
    _require_non_empty_string(shard_id, "shard_id")
    _require_non_empty_string(chart_id, "chart_id")
    if not isinstance(start_address, HexAddress):
        raise ValueError("start_address must be a HexAddress")
    _require_non_negative_int(max_layers, "max_layers")
    _require_non_negative_int(radius, "radius")
    steps = []
    for layer in range(start_address.layer, start_address.layer + max_layers + 1):
        addresses = tuple(
            HexAddress(layer, axial.q, axial.r)
            for axial in axial_disk(Axial(start_address.q, start_address.r), radius)
        )
        steps.append(
            ScaleScanStep(
                layer=layer,
                chart_id=chart_id,
                addresses=addresses,
                reason="linear scale scan candidate step",
            )
        )
    return ScaleScanPlan(
        plan_id=f"scale-scan:{shard_id}:{chart_id}:{start_address.uri()}:{max_layers}:{radius}",
        shard_id=shard_id,
        steps=tuple(steps),
        stop_reason="max_layers_reached",
    )


def validate_scale_scan_step(step: ScaleScanStep) -> None:
    if not isinstance(step, ScaleScanStep):
        raise ValueError("step must be a ScaleScanStep")
    ScaleScanStep(step.layer, step.chart_id, step.addresses, step.reason)


def validate_scale_scan_plan(plan: ScaleScanPlan) -> None:
    if not isinstance(plan, ScaleScanPlan):
        raise ValueError("plan must be a ScaleScanPlan")
    ScaleScanPlan(plan.plan_id, plan.shard_id, plan.steps, plan.stop_reason, plan.status)


def scale_scan_plan_to_record(plan: ScaleScanPlan) -> dict[str, object]:
    validate_scale_scan_plan(plan)
    return {
        "plan_id": plan.plan_id,
        "shard_id": plan.shard_id,
        "steps": [_step_to_record(step) for step in plan.steps],
        "stop_reason": plan.stop_reason,
        "status": plan.status,
    }


def scale_scan_plan_from_record(record: Mapping[str, object]) -> ScaleScanPlan:
    if not isinstance(record, Mapping):
        raise ValueError("record must be a mapping")
    steps_record = record.get("steps")
    if not isinstance(steps_record, list):
        raise ValueError("steps must be a list")
    return ScaleScanPlan(
        plan_id=_record_string(record, "plan_id"),
        shard_id=_record_string(record, "shard_id"),
        steps=tuple(_step_from_record(step) for step in steps_record),
        stop_reason=_record_string(record, "stop_reason"),
        status=_record_string(record, "status", "candidate"),
    )


def _step_to_record(step: ScaleScanStep) -> dict[str, object]:
    return {
        "layer": step.layer,
        "chart_id": step.chart_id,
        "addresses": [
            {"layer": address.layer, "q": address.q, "r": address.r}
            for address in step.addresses
        ],
        "reason": step.reason,
    }


def _step_from_record(record: object) -> ScaleScanStep:
    if not isinstance(record, Mapping):
        raise ValueError("step must be a mapping")
    addresses_record = record.get("addresses")
    if not isinstance(addresses_record, list):
        raise ValueError("addresses must be a list")
    return ScaleScanStep(
        layer=_record_non_negative_int(record, "layer"),
        chart_id=_record_string(record, "chart_id"),
        addresses=tuple(_address_from_record(item) for item in addresses_record),
        reason=_record_string(record, "reason"),
    )


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


__all__ = [
    "ALLOWED_SCALE_SCAN_STATUSES",
    "ScaleScanStep",
    "ScaleScanPlan",
    "make_linear_scale_scan_plan",
    "validate_scale_scan_step",
    "validate_scale_scan_plan",
    "scale_scan_plan_to_record",
    "scale_scan_plan_from_record",
]
