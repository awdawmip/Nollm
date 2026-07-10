"""Computed GRF gate evidence and predicate evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

OPERATORS = frozenset({"eq", "ne", "ge", "gt", "le", "lt", "truthy", "falsy"})


@dataclass(frozen=True)
class GatePredicate:
    predicate: str
    measured_value: object
    required_value: object
    operator: str

    def __post_init__(self) -> None:
        if not isinstance(self.predicate, str) or not self.predicate:
            raise ValueError("predicate must be non-empty text")
        if self.operator not in OPERATORS:
            raise ValueError("unsupported gate predicate operator")

    @property
    def passed(self) -> bool:
        left, right = self.measured_value, self.required_value
        if self.operator == "eq":
            return left == right
        if self.operator == "ne":
            return left != right
        if self.operator == "ge":
            return _ordered(left, right, lambda a, b: a >= b)
        if self.operator == "gt":
            return _ordered(left, right, lambda a, b: a > b)
        if self.operator == "le":
            return _ordered(left, right, lambda a, b: a <= b)
        if self.operator == "lt":
            return _ordered(left, right, lambda a, b: a < b)
        if self.operator == "truthy":
            return bool(left)
        return not bool(left)

    def to_mapping(self) -> dict[str, object]:
        return {
            "predicate": self.predicate,
            "measured_value": self.measured_value,
            "required_value": self.required_value,
            "operator": self.operator,
            "pass": self.passed,
        }

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "GatePredicate":
        predicate = cls(payload["predicate"], payload.get("measured_value"), payload.get("required_value"), payload["operator"])
        if "pass" in payload and payload["pass"] is not predicate.passed:
            raise ValueError("stored predicate pass value is not reproducible")
        return predicate


@dataclass(frozen=True)
class GateResult:
    gate: str
    predicates: tuple[GatePredicate, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.gate, str) or not self.gate:
            raise ValueError("gate must be non-empty text")
        if not self.predicates:
            raise ValueError("gate must contain predicates")

    @property
    def passed(self) -> bool:
        return all(item.passed for item in self.predicates)

    @property
    def status(self) -> str:
        return f"GATE_{self.gate}_{'PASS' if self.passed else 'FAIL'}"


@dataclass(frozen=True)
class GateEvidence:
    gate: str
    source_raw_path: str
    measurements: dict[str, object]
    predicates: tuple[GatePredicate, ...]
    event_count: int

    def __post_init__(self) -> None:
        if not isinstance(self.source_raw_path, str) or not self.source_raw_path:
            raise ValueError("source_raw_path must be non-empty text")
        if type(self.event_count) is not int or self.event_count < 0:
            raise ValueError("event_count must be non-negative integer")

    @property
    def result(self) -> GateResult:
        return GateResult(self.gate, self.predicates)

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": "grf7r_gate_evidence_v1",
            "gate": self.gate,
            "source_raw_path": self.source_raw_path,
            "measurements": self.measurements,
            "event_count": self.event_count,
            "predicates": tuple(item.to_mapping() for item in self.predicates),
            "status": self.result.status,
        }

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "GateEvidence":
        if payload.get("schema") != "grf7r_gate_evidence_v1":
            raise ValueError("gate evidence schema mismatch")
        evidence = cls(payload["gate"], payload["source_raw_path"], dict(payload["measurements"]), tuple(GatePredicate.from_mapping(item) for item in payload["predicates"]), payload["event_count"])
        if payload.get("status") != evidence.result.status:
            raise ValueError("stored gate status is not reproducible")
        return evidence


def _ordered(left: object, right: object, operation) -> bool:
    if type(left) not in (int, float) or type(right) not in (int, float):
        raise TypeError("ordered gate predicates require numeric values")
    return bool(operation(left, right))
