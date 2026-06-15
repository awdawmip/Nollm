from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Iterable, Mapping


@dataclass(frozen=True)
class ParameterRegime:
    regime_id: str
    beta: float
    theta_deg: float
    description: str

    def __post_init__(self) -> None:
        _require_non_empty_string(self.regime_id, "regime_id")
        _require_positive_number(self.beta, "beta")
        _require_positive_number(self.theta_deg, "theta_deg")
        _require_non_empty_string(self.description, "description")


@dataclass(frozen=True)
class ParameterExperimentResult:
    regime_id: str
    layers: int
    rotation_cycle_hit: bool
    side_length_ratio_after_layers: float
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_non_empty_string(self.regime_id, "regime_id")
        _require_non_negative_int(self.layers, "layers")
        if not isinstance(self.rotation_cycle_hit, bool):
            raise ValueError("rotation_cycle_hit must be a boolean")
        _require_positive_number(
            self.side_length_ratio_after_layers,
            "side_length_ratio_after_layers",
        )
        object.__setattr__(self, "notes", tuple(self.notes))
        for note in self.notes:
            _require_non_empty_string(note, "note")


def default_parameter_regimes() -> tuple[ParameterRegime, ...]:
    phi = (1 + sqrt(5)) / 2
    return (
        ParameterRegime("beta_2q_15", 2 ** 0.25, 15.0, "2^(1/4) + 15 deg"),
        ParameterRegime("beta_2q_22_5", 2 ** 0.25, 22.5, "2^(1/4) + 22.5 deg"),
        ParameterRegime("sqrt2_15", sqrt(2), 15.0, "sqrt(2) + 15 deg"),
        ParameterRegime("phi_15", phi, 15.0, "phi + 15 deg"),
        ParameterRegime("sqrt3_30_benchmark", sqrt(3), 30.0, "sqrt(3) + 30 deg benchmark"),
    )


def evaluate_parameter_regime(regime: ParameterRegime, layers: int) -> ParameterExperimentResult:
    if not isinstance(regime, ParameterRegime):
        raise ValueError("regime must be a ParameterRegime")
    _require_non_negative_int(layers, "layers")
    rotation = (layers * regime.theta_deg) % 60.0
    return ParameterExperimentResult(
        regime_id=regime.regime_id,
        layers=layers,
        rotation_cycle_hit=abs(rotation) < 1e-12 or abs(rotation - 60.0) < 1e-12,
        side_length_ratio_after_layers=regime.beta ** (-layers),
        notes=("deterministic diagnostic",),
    )


def rank_parameter_results(
    results: Iterable[ParameterExperimentResult],
) -> list[ParameterExperimentResult]:
    items = list(results)
    for item in items:
        if not isinstance(item, ParameterExperimentResult):
            raise ValueError("results must contain ParameterExperimentResult instances")
    return sorted(
        items,
        key=lambda result: (
            not result.rotation_cycle_hit,
            result.layers,
            result.side_length_ratio_after_layers,
            result.regime_id,
        ),
    )


def parameter_regime_to_record(regime: ParameterRegime) -> dict[str, object]:
    if not isinstance(regime, ParameterRegime):
        raise ValueError("regime must be a ParameterRegime")
    return {
        "regime_id": regime.regime_id,
        "beta": regime.beta,
        "theta_deg": regime.theta_deg,
        "description": regime.description,
    }


def parameter_regime_from_record(record: Mapping[str, object]) -> ParameterRegime:
    if not isinstance(record, Mapping):
        raise ValueError("record must be a mapping")
    return ParameterRegime(
        regime_id=_record_string(record, "regime_id"),
        beta=_record_number(record, "beta"),
        theta_deg=_record_number(record, "theta_deg"),
        description=_record_string(record, "description"),
    )


def parameter_result_to_record(result: ParameterExperimentResult) -> dict[str, object]:
    if not isinstance(result, ParameterExperimentResult):
        raise ValueError("result must be a ParameterExperimentResult")
    return {
        "regime_id": result.regime_id,
        "layers": result.layers,
        "rotation_cycle_hit": result.rotation_cycle_hit,
        "side_length_ratio_after_layers": result.side_length_ratio_after_layers,
        "notes": list(result.notes),
    }


def parameter_result_from_record(record: Mapping[str, object]) -> ParameterExperimentResult:
    if not isinstance(record, Mapping):
        raise ValueError("record must be a mapping")
    notes = record.get("notes", ())
    if not isinstance(notes, (list, tuple)):
        raise ValueError("notes must be a list or tuple")
    return ParameterExperimentResult(
        regime_id=_record_string(record, "regime_id"),
        layers=_record_non_negative_int(record, "layers"),
        rotation_cycle_hit=_record_bool(record, "rotation_cycle_hit"),
        side_length_ratio_after_layers=_record_number(record, "side_length_ratio_after_layers"),
        notes=tuple(notes),
    )


def _require_non_empty_string(value: str, label: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")


def _require_positive_number(value: float, label: str) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"{label} must be a positive number")


def _require_non_negative_int(value: int, label: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")


def _record_string(record: Mapping[str, object], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return value


def _record_number(record: Mapping[str, object], key: str) -> float:
    value = record.get(key)
    _require_positive_number(value, key)  # type: ignore[arg-type]
    return float(value)


def _record_non_negative_int(record: Mapping[str, object], key: str) -> int:
    value = record.get(key)
    _require_non_negative_int(value, key)  # type: ignore[arg-type]
    return value  # type: ignore[return-value]


def _record_bool(record: Mapping[str, object], key: str) -> bool:
    value = record.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"{key} must be a boolean")
    return value


__all__ = [
    "ParameterRegime",
    "ParameterExperimentResult",
    "default_parameter_regimes",
    "evaluate_parameter_regime",
    "rank_parameter_results",
    "parameter_regime_to_record",
    "parameter_regime_from_record",
    "parameter_result_to_record",
    "parameter_result_from_record",
]
