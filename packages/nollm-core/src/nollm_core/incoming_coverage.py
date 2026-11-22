"""Complete local inverse candidates for the fixed sampled ``coverage_up``.

This inverts the *source* stencil. A parent's independently sampled
``coverage_down`` is not an enumeration of all sources that hit it.
No incoming relation is persisted; every result derives from geometry.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from .approximate_coverage import (
    _Q40_ONE,
    _TRANSFORMS,
    _compiled_sample_offsets_q40,
    _validate,
    expand_approximate_coverage,
)
from .coverage_contract import MAX_ACTIVE_HEX_RADIUS, UnsupportedPhysicalCoverage
from .geometry import GeometryAddress


# Three times the vertices of |2q+r|, |q+2r|, |q-r| <= 1.
_HEX_THIRDS = ((1, 1), (-1, 2), (-2, 1), (-1, -1), (1, -2), (2, -1))


@dataclass(frozen=True)
class IncomingCoverageMember:
    source: GeometryAddress
    weight_q16: int
    hit_count: int


@dataclass(frozen=True)
class IncomingCoverage:
    parent: GeometryAddress
    members: tuple[IncomingCoverageMember, ...]
    candidate_count: int
    complete: bool
    unavailable_sources: tuple[GeometryAddress, ...] = ()


@lru_cache(maxsize=1)
def _inverse_bounds() -> tuple[int, tuple[tuple[int, int, int, int], ...]]:
    """Compile exact interval numerators once; all arithmetic is integer.

    M n + o_j - S parent lies in S H at every possible hit. For each row
    (a,b)/det(M) of M^-1, extrema over H's six vertices and all offsets give
    an enclosing interval. Its common denominator below is 3*det(M).
    The current two interval widths are both strictly less than three, so
    each interval contains at most three integer child coordinates.
    """
    a, b, c, d = _TRANSFORMS["coverage_up"][:4]
    determinant = a * d - b * c
    offsets = _compiled_sample_offsets_q40("coverage_up")
    rows = []
    for x, y in ((d, -b), (-c, a)):
        hex_extrema = [x * q + y * r for q, r in _HEX_THIRDS]
        offset_extrema = [x * q + y * r for q, r in offsets]
        lower = _Q40_ONE * min(hex_extrema) - 3 * max(offset_extrema)
        upper = _Q40_ONE * max(hex_extrema) - 3 * min(offset_extrema)
        rows.append((x, y, lower, upper))
    return 3 * determinant, tuple(rows)


def incoming_coverage_candidates(parent: GeometryAddress) -> tuple[GeometryAddress, ...]:
    """Return every admitted child that could send sampled up mass to parent.

    At most nine candidates under the current fixed kernel. Closed bounds
    retain ties; the existing rounder decides their actual membership.
    Sources outside the storage domain cannot contain admitted material and
    are omitted. A parent without an admitted finer layer raises the same
    UnsupportedPhysicalCoverage used by outgoing coverage.
    """
    _validate(parent, "coverage_down")
    denominator, rows = _inverse_bounds()
    intervals = []
    for a, b, lower, upper in rows:
        center = 3 * _Q40_ONE * (a * parent.q + b * parent.r)
        # ceil(lower endpoint) .. floor(upper endpoint), including equality.
        first = -(-(center + lower) // denominator)
        last = (center + upper) // denominator
        intervals.append(range(first, last + 1))
    return tuple(
        GeometryAddress(parent.profile_id, parent.chart_id, parent.layer + 1, q, r, parent.phase)
        for q in intervals[0]
        for r in intervals[1]
        if max(abs(q), abs(r), abs(q + r)) <= MAX_ACTIVE_HEX_RADIUS
    )


def incoming_coverage(parent: GeometryAddress) -> IncomingCoverage:
    """Filter inverse candidates with the unchanged native up kernel.

    Source weights retain their original normalization over *all* parents.
    A source whose native expansion reaches outside the storage contract is
    reported as unavailable, rather than silently called empty or renormalized.
    """
    candidates = incoming_coverage_candidates(parent)
    members = []
    unavailable = []
    for source in candidates:
        try:
            expansion = expand_approximate_coverage(source, "coverage_up")
        except UnsupportedPhysicalCoverage:
            unavailable.append(source)
            continue
        for member in expansion.members:
            if member.target == parent:
                members.append(IncomingCoverageMember(source, member.weight_q16, member.hit_count))
                break
    return IncomingCoverage(parent, tuple(members), len(candidates), not unavailable, tuple(unavailable))
