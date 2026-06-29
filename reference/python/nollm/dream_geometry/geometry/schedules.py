"""Parameter schedules for DG1 V2 geometry validation.

Allowed: pure scale/rotation/phase parameter objects for reproducible finite
geometry experiments.
Forbidden: selecting production defaults, runtime integration, Field, Cortex,
Recall, Adapter, V1, OpenClaw, filesystem, network, subprocess, or memory
behavior.
"""

from dataclasses import dataclass
from math import cos, pi, sin, sqrt

from .types import LocalChart, Vec2


@dataclass(frozen=True)
class ParameterSet:
    parameter_id: str
    beta: float
    delta_theta_degrees: float
    role: str

    def __post_init__(self) -> None:
        if self.beta <= 1.0:
            raise ValueError("beta must be greater than one")


@dataclass(frozen=True)
class PhaseSchedule:
    phase_q: float
    phase_r: float


@dataclass(frozen=True)
class ScaleRotationSchedule:
    parameter_set: ParameterSet
    s0: float = 1.0
    theta0_degrees: float = 0.0

    def side_length(self, layer_index: int) -> float:
        _require_layer(layer_index)
        return self.s0 * (self.parameter_set.beta ** (-layer_index))

    def rotation_degrees(self, layer_index: int) -> float:
        _require_layer(layer_index)
        return self.theta0_degrees + layer_index * self.parameter_set.delta_theta_degrees

    def rotation_radians(self, layer_index: int) -> float:
        return self.rotation_degrees(layer_index) * pi / 180.0

    def chart_for_layer(self, layer_index: int, phase: PhaseSchedule = PhaseSchedule(0.0, 0.0)) -> LocalChart:
        side = self.side_length(layer_index)
        rotation = self.rotation_radians(layer_index)
        # Convert fractional axial phase into world translation using the same
        # Eisenstein normalization as chart axial_to_world.
        reference_x = phase.phase_q + phase.phase_r / 2.0
        reference_y = sqrt(3.0) * phase.phase_r / 2.0
        scale = sqrt(3.0) * side
        unrotated = Vec2(reference_x * scale, reference_y * scale)
        c = cos(rotation)
        s = sin(rotation)
        translation = Vec2(unrotated.x * c - unrotated.y * s, unrotated.x * s + unrotated.y * c)
        return LocalChart(
            chart_id=f"{self.parameter_set.parameter_id}_L{layer_index}_P{phase.phase_q:g}_{phase.phase_r:g}",
            layer_index=layer_index,
            side_length=side,
            rotation_radians=rotation,
            translation=translation,
            phase_metadata={"parameter_id": self.parameter_set.parameter_id, "role": self.parameter_set.role},
        )


PARAMETER_MATRIX: tuple[ParameterSet, ...] = (
    ParameterSet("A", 2.0 ** 0.25, 15.0, "slow densification engineering control"),
    ParameterSet("B", 2.0 ** 0.25, 22.5, "current engineering baseline"),
    ParameterSet("C", sqrt(2.0), 15.0, "medium-speed engineering control"),
    ParameterSet("D", (1.0 + sqrt(5.0)) / 2.0, 15.0, "research model"),
    ParameterSet("E", sqrt(3.0), 30.0, "Eisenstein arithmetic benchmark"),
)


DEFAULT_PHASE_SAMPLES: tuple[PhaseSchedule, ...] = (
    PhaseSchedule(0.0, 0.0),
    PhaseSchedule(0.5, 0.0),
    PhaseSchedule(1.0 / 3.0, 1.0 / 3.0),
    PhaseSchedule(1.0 / 5.0, 2.0 / 5.0),
)


def schedules_for_matrix() -> tuple[ScaleRotationSchedule, ...]:
    return tuple(ScaleRotationSchedule(parameter) for parameter in PARAMETER_MATRIX)


def _require_layer(layer_index: int) -> None:
    if not isinstance(layer_index, int) or isinstance(layer_index, bool) or layer_index < 0:
        raise ValueError("layer_index must be a non-negative integer")


__all__ = [
    "DEFAULT_PHASE_SAMPLES",
    "PARAMETER_MATRIX",
    "ParameterSet",
    "PhaseSchedule",
    "ScaleRotationSchedule",
    "schedules_for_matrix",
]
