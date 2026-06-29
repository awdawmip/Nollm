"""Immutable numeric types for the DG1 V2 geometry kernel.

Allowed: small frozen dataclasses for pure geometry values and metadata.
Forbidden: Evidence, Field, Cortex, Recall, Adapter, V1, OpenClaw, runtime,
filesystem, network, subprocess, or memory behavior.
"""

from dataclasses import dataclass
from math import isfinite, sqrt
from types import MappingProxyType
from typing import Mapping


DEFAULT_NUMERIC_MODE = "float64_tolerance"


@dataclass(frozen=True, order=True)
class Vec2:
    """Two-dimensional float vector."""

    x: float
    y: float

    def __post_init__(self) -> None:
        _require_finite_number(self.x, "x")
        _require_finite_number(self.y, "y")

    def __add__(self, other: "Vec2") -> "Vec2":
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Vec2") -> "Vec2":
        return Vec2(self.x - other.x, self.y - other.y)

    def scale(self, factor: float) -> "Vec2":
        _require_finite_number(factor, "factor")
        return Vec2(self.x * factor, self.y * factor)

    def dot(self, other: "Vec2") -> float:
        return self.x * other.x + self.y * other.y

    def cross(self, other: "Vec2") -> float:
        return self.x * other.y - self.y * other.x

    def norm(self) -> float:
        return (self.x * self.x + self.y * self.y) ** 0.5

    def to_complex(self) -> complex:
        return complex(self.x, self.y)

    @classmethod
    def from_complex(cls, value: complex) -> "Vec2":
        return cls(float(value.real), float(value.imag))


@dataclass(frozen=True, order=True)
class AxialCoord:
    """Axial hex-grid coordinate."""

    q: int
    r: int

    def __post_init__(self) -> None:
        _require_int(self.q, "q")
        _require_int(self.r, "r")


@dataclass(frozen=True, order=True)
class CubeCoord:
    """Cube hex-grid coordinate with x + y + z == 0."""

    x: int
    y: int
    z: int

    def __post_init__(self) -> None:
        _require_int(self.x, "x")
        _require_int(self.y, "y")
        _require_int(self.z, "z")
        if self.x + self.y + self.z != 0:
            raise ValueError("cube coordinates must satisfy x + y + z == 0")


@dataclass(frozen=True, order=True)
class CellRef:
    """Stable cell identity inside one local chart."""

    chart_id: str
    axial: AxialCoord

    def __post_init__(self) -> None:
        _require_non_empty_string(self.chart_id, "chart_id")


@dataclass(frozen=True)
class GeometryTolerance:
    """Float comparison tolerances used by DG1 geometry operations."""

    coordinate_abs_tol: float = 1e-12
    coordinate_rel_tol: float = 1e-10
    area_abs_tol: float = 1e-12
    area_rel_tol: float = 1e-10

    def __post_init__(self) -> None:
        for label, value in (
            ("coordinate_abs_tol", self.coordinate_abs_tol),
            ("coordinate_rel_tol", self.coordinate_rel_tol),
            ("area_abs_tol", self.area_abs_tol),
            ("area_rel_tol", self.area_rel_tol),
        ):
            _require_non_negative_number(value, label)


@dataclass(frozen=True)
class ComputationMetadata:
    """Numeric metadata carried by geometric outputs."""

    numeric_mode: str
    absolute_tolerance: float
    relative_tolerance: float
    comparison_scale: float

    def __post_init__(self) -> None:
        _require_non_empty_string(self.numeric_mode, "numeric_mode")
        _require_non_negative_number(self.absolute_tolerance, "absolute_tolerance")
        _require_non_negative_number(self.relative_tolerance, "relative_tolerance")
        _require_positive_number(self.comparison_scale, "comparison_scale")


@dataclass(frozen=True)
class PhaseCoord:
    """Normalized chart phase coordinate in the [0, 1) torus."""

    q: float
    r: float

    def __post_init__(self) -> None:
        _require_finite_number(self.q, "q")
        _require_finite_number(self.r, "r")
        if not 0.0 <= self.q < 1.0:
            raise ValueError("phase q must be in [0, 1)")
        if not 0.0 <= self.r < 1.0:
            raise ValueError("phase r must be in [0, 1)")


@dataclass(frozen=True)
class HexCell:
    """One concrete hex cell in one local chart."""

    cell_ref: CellRef
    center: Vec2
    side_length: float
    rotation_radians: float
    vertices: tuple[Vec2, ...]
    metadata: ComputationMetadata

    def __post_init__(self) -> None:
        _require_positive_number(self.side_length, "side_length")
        _require_finite_number(self.rotation_radians, "rotation_radians")
        if len(self.vertices) != 6:
            raise ValueError("HexCell vertices must contain exactly six points")

    @property
    def area(self) -> float:
        return 3.0 * sqrt(3.0) * self.side_length * self.side_length / 2.0


@dataclass(frozen=True)
class LocalChart:
    """Pure local chart definition for DG1 geometry."""

    chart_id: str
    layer_index: int
    side_length: float
    rotation_radians: float
    translation: Vec2
    phase_metadata: Mapping[str, str] = MappingProxyType({})

    def __post_init__(self) -> None:
        _require_non_empty_string(self.chart_id, "chart_id")
        _require_int(self.layer_index, "layer_index")
        _require_positive_number(self.side_length, "side_length")
        _require_finite_number(self.rotation_radians, "rotation_radians")
        object.__setattr__(self, "phase_metadata", MappingProxyType(dict(self.phase_metadata)))


def _require_int(value: int, label: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{label} must be an integer")


def _require_non_empty_string(value: str, label: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")


def _require_finite_number(value: float, label: str) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not isfinite(float(value)):
        raise ValueError(f"{label} must be a finite number")


def _require_non_negative_number(value: float, label: str) -> None:
    _require_finite_number(value, label)
    if float(value) < 0:
        raise ValueError(f"{label} must be non-negative")


def _require_positive_number(value: float, label: str) -> None:
    _require_finite_number(value, label)
    if float(value) <= 0:
        raise ValueError(f"{label} must be positive")


DEFAULT_TOLERANCE = GeometryTolerance()


def default_metadata(
    *,
    tolerance: GeometryTolerance = DEFAULT_TOLERANCE,
    comparison_scale: float = 1.0,
    area: bool = False,
) -> ComputationMetadata:
    """Build standard DG1 float metadata."""

    return ComputationMetadata(
        numeric_mode=DEFAULT_NUMERIC_MODE,
        absolute_tolerance=tolerance.area_abs_tol if area else tolerance.coordinate_abs_tol,
        relative_tolerance=tolerance.area_rel_tol if area else tolerance.coordinate_rel_tol,
        comparison_scale=comparison_scale,
    )


__all__ = [
    "DEFAULT_NUMERIC_MODE",
    "DEFAULT_TOLERANCE",
    "AxialCoord",
    "CellRef",
    "ComputationMetadata",
    "CubeCoord",
    "GeometryTolerance",
    "HexCell",
    "LocalChart",
    "PhaseCoord",
    "Vec2",
    "default_metadata",
]
