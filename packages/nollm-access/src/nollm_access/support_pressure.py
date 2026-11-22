"""Advisory write pressure from local, current, geometrically allocated material.

This module does not choose a write target or change admission/recall weights.
The caller supplies current physical identities, not observation counts or
statement-history rows, while holding its usual consistent-read lease.
"""
from __future__ import annotations

from collections.abc import Callable, Hashable, Iterable
from dataclasses import dataclass

from nollm_core import GeometryAddress, Q16_ONE, UnsupportedPhysicalCoverage, incoming_coverage


UnitsAt = Callable[[GeometryAddress], Iterable[Hashable] | None]


@dataclass(frozen=True)
class WritePressure:
    cell: GeometryAddress
    current_units: int | None
    additions: int
    demand_units: int | None
    support_q16: int
    pressure: int | None
    write_weight: int | None
    support_complete: bool
    unknown_cells: tuple[GeometryAddress, ...] = ()
    geometry_error: str | None = None

    @property
    def demand_complete(self) -> bool:
        return self.demand_units is not None

    @property
    def score_kind(self) -> str:
        if not self.demand_complete:
            return "demand_unknown"
        return "complete_native_support" if self.support_complete else "upper_estimate"

    def to_mapping(self) -> dict[str, object]:
        return {
            "cell": self.cell.to_mapping(),
            "current_units": self.current_units,
            "additions": self.additions,
            "demand_units": self.demand_units,
            "support_q16": self.support_q16,
            "pressure": self.pressure,
            "write_weight": self.write_weight,
            "support_complete": self.support_complete,
            "demand_complete": self.demand_complete,
            "score_kind": self.score_kind,
            "unknown_cells": [cell.to_mapping() for cell in self.unknown_cells],
            "geometry_error": self.geometry_error,
            "advisory": True,
        }


def pressure_score(demand_units: int, support_q16: int, kappa: int = 1) -> int:
    """Round 1 + 99*(D-S)+/(D+kappa) half upward, using integer units/Q16.

    Kappa is a positive cold-start scale in the same unit as demand. It does
    not add support. Display rounding gives non-strict monotonic plateaus.
    """
    if not isinstance(demand_units, int) or demand_units < 0:
        raise ValueError("demand_units must be a nonnegative integer")
    if not isinstance(support_q16, int) or support_q16 < 0:
        raise ValueError("support_q16 must be a nonnegative integer")
    if not isinstance(kappa, int) or kappa <= 0:
        raise ValueError("kappa must be a positive integer")
    return _score_from_counts(demand_units, support_q16, kappa)


def _score_from_counts(demand_units: int, support_q16: int, kappa: int) -> int:
    deficit_q16 = max(demand_units * Q16_ONE - support_q16, 0)
    denominator = (demand_units + kappa) * Q16_ONE
    return 1 + (2 * 99 * deficit_q16 + denominator) // (2 * denominator)


def write_pressure(
    cell: GeometryAddress,
    units_at: UnitsAt,
    *,
    additions: int = 1,
    kappa: int = 1,
) -> WritePressure:
    """Evaluate one candidate after the proposed number of new material units.

    Supply additions=0 for observation, reuse or an in-place revision. A
    callback returning None means unobserved, not known empty. Repeated
    identities within a cell count once; identities must name their actual
    current physical placement (AtomHandle is suitable). An identity cannot
    simultaneously name two different lower physical placements.

    With known demand and incomplete support, the returned score is an upper
    estimate. Unknown demand produces no score, since its error would have the
    opposite monotonic direction. No recursive pressure propagation occurs.
    """
    if not isinstance(additions, int) or additions < 0:
        raise ValueError("additions must be a nonnegative integer")
    if not isinstance(kappa, int) or kappa <= 0:
        raise ValueError("kappa must be a positive integer")
    current = units_at(cell)
    current_units = None if current is None else len(set(current))
    demand = None if current_units is None else current_units + additions
    support = 0
    unknown = []
    geometry_error = None
    try:
        incoming = incoming_coverage(cell)
    except UnsupportedPhysicalCoverage as error:
        complete = False
        geometry_error = str(error)
    else:
        complete = incoming.complete
        unknown.extend(incoming.unavailable_sources)
        owners: dict[Hashable, GeometryAddress] = {}
        for member in incoming.members:
            units = units_at(member.source)
            if units is None:
                complete = False
                unknown.append(member.source)
                continue
            unique = set(units)
            for unit in unique:
                if unit in owners and owners[unit] != member.source:
                    raise ValueError("a current unit identity was reported in two lower cells")
                owners[unit] = member.source
            support += len(unique) * member.weight_q16
    score = None if demand is None else _score_from_counts(demand, support, kappa)
    return WritePressure(
        cell, current_units, additions, demand, support, score,
        None if score is None else 101 - score,
        complete, tuple(unknown), geometry_error,
    )
