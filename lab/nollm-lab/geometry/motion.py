"""Exact reuse of the current Q40 sample footprint under translation.

This Lab component evaluates hypothetical motion, without changing Core state
or its fixed geometry contract. It preserves the original nearest-cell tie
rule and Q16 normalization. Raw target coordinates are diagnostic; a caller
that persists cells must still apply the storage domain's admission rules.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace
from fractions import Fraction

from nollm_core import (
    GeometryAddress,
    coverage_stencil_q40,
    nearest_axial_q40,
    normalize_q16_weights,
)


Q40_ONE = 1 << 40
MOTION_CONTRACT_ID = "lab_q40_translation_reuse_v1"
NORMALS = ((2, 1), (1, 2), (-1, 1), (-2, -1), (-1, -2), (1, -1))
Point = tuple[int, int]
# The exploratory timing found selective maintenance slower on large jumps.
# This affects work selection only; both paths produce the same exact result.
REBUILD_DISTANCE_Q40 = Q40_ONE // 16
_ORIGIN = GeometryAddress("default_dream_v1", "default", 0, 0, 0)


def _margins(point: Point, target: Point) -> tuple[int, ...]:
    q = point[0] - Q40_ONE * target[0]
    r = point[1] - Q40_ONE * target[1]
    return tuple(Q40_ONE - hq * q - hr * r for hq, hr in NORMALS)


def _counts(targets: tuple[Point, ...]) -> tuple[tuple[int, int, int, int], ...]:
    counts = sorted(Counter(targets).items())
    weights = normalize_q16_weights([count for _, count in counts])
    return tuple((q, r, count, weight)
                 for ((q, r), count), weight in zip(counts, weights))


def _split_even(delta: int) -> tuple[int, int]:
    block, residual = divmod(delta + Q40_ONE, 2 * Q40_ONE)
    return 2 * block, residual - Q40_ONE


@dataclass(frozen=True)
class MotionStep:
    footprint: "TranslationFootprint"
    mode: str
    round_calls: int
    changed_samples: int


@dataclass(frozen=True)
class TranslationFootprint:
    """An immutable translated stencil and a reusable six-face certificate.

    The anchor is always even. Certificate arrays stay shared while only the
    accumulated shift changes; a successful six-face test therefore does not
    update 96 point arrays. On crossings, a new local certificate is built.
    """

    direction: str
    anchor: Point
    _base_center: Point
    _points: tuple[Point, ...]
    _targets: tuple[Point, ...]
    _margins: tuple[tuple[int, ...], ...]
    _minima: tuple[int, ...]
    _counts_q16: tuple[tuple[int, int, int, int], ...]
    _shift: Point = (0, 0)

    @classmethod
    def from_source(cls, source: GeometryAddress, direction: str) -> "TranslationFootprint":
        stencil = coverage_stencil_q40(source, direction)
        return cls._from_center(direction, stencil.center_q40, stencil.offsets_q40)

    @classmethod
    def from_center_q40(cls, direction: str, center: Point) -> "TranslationFootprint":
        stencil = coverage_stencil_q40(_ORIGIN, direction)
        return cls._from_center(direction, center, stencil.offsets_q40)

    @classmethod
    def _from_center(cls, direction, center, offsets):
        bq, pq = divmod(center[0], 2 * Q40_ONE)
        br, pr = divmod(center[1], 2 * Q40_ONE)
        points = tuple((pq + dq, pr + dr) for dq, dr in offsets)
        targets = tuple(nearest_axial_q40(*point) for point in points)
        return cls._build(direction, (2 * bq, 2 * br), (pq, pr), points, targets)

    @classmethod
    def _build(cls, direction, anchor, center, points, targets):
        margins = tuple(_margins(point, target) for point, target in zip(points, targets))
        minima = tuple(min(row[i] for row in margins) for i in range(6))
        return cls(direction, anchor, center, points, targets, margins, minima, _counts(targets))

    @property
    def center_q40(self) -> Point:
        return (self.anchor[0] * Q40_ONE + self._base_center[0] + self._shift[0],
                self.anchor[1] * Q40_ONE + self._base_center[1] + self._shift[1])

    def sample_targets(self) -> tuple[Point, ...]:
        aq, ar = self.anchor
        return tuple((q + aq, r + ar) for q, r in self._targets)

    def counts_q16(self) -> tuple[tuple[int, int, int, int], ...]:
        """Return sorted (q, r, hit_count, weight_q16) records."""
        aq, ar = self.anchor
        return tuple((q + aq, r + ar, count, weight)
                     for q, r, count, weight in self._counts_q16)

    def next_boundary(self, direction_q40: Point) -> Fraction | None:
        """First possible sample boundary along current point + t*direction.

        A zero result means a current point is on a relevant boundary; evaluate
        both sides with the original rounder. None denotes zero motion.
        """
        times = []
        for (hq, hr), margin in zip(NORMALS, self._minima):
            velocity = hq * direction_q40[0] + hr * direction_q40[1]
            if velocity > 0:
                remaining = margin - hq * self._shift[0] - hr * self._shift[1]
                times.append(Fraction(remaining, velocity))
        return min(times) if times else None

    def translate(self, delta_q40: Point, *, mode: str = "auto") -> MotionStep:
        """Evaluate a translation relative to this footprint.

        ``auto`` reuses safe certificates, recomputes crossing points on small
        changes, and rebuilds on large changes. ``full`` recomputes every point
        and serves as a direct comparison path. Only even whole-cell shifts
        are factored out; an odd-cell shift still uses the original tie rule.
        """
        if mode not in {"auto", "full"}:
            raise ValueError("mode must be auto or full")
        aq, dq = _split_even(delta_q40[0])
        ar, dr = _split_even(delta_q40[1])
        anchor = (self.anchor[0] + aq, self.anchor[1] + ar)
        shift = (self._shift[0] + dq, self._shift[1] + dr)
        if mode == "auto" and (dq, dr) == (0, 0):
            state = self if anchor == self.anchor else replace(self, anchor=anchor)
            return MotionStep(state, "reuse", 0, len(self._targets) if (aq or ar) else 0)

        projections = tuple(hq * shift[0] + hr * shift[1] for hq, hr in NORMALS)
        if mode == "auto" and all(p < m for p, m in zip(projections, self._minima)):
            return MotionStep(replace(self, anchor=anchor, _shift=shift), "reuse", 0,
                              len(self._targets) if (aq or ar) else 0)

        points = tuple((q + shift[0], r + shift[1]) for q, r in self._points)
        distance = max(abs(shift[0]), abs(shift[1]), abs(shift[0] + shift[1]))
        full = mode == "full" or distance >= REBUILD_DISTANCE_Q40
        if full:
            targets = tuple(nearest_axial_q40(*point) for point in points)
            calls = len(points)
        else:
            updated = list(self._targets)
            calls = 0
            for i, (point, margins) in enumerate(zip(points, self._margins)):
                if not all(p < m for p, m in zip(projections, margins)):
                    updated[i] = nearest_axial_q40(*point)
                    calls += 1
            targets = tuple(updated)
        changed = sum((q + aq, r + ar) != old
                      for (q, r), old in zip(targets, self._targets))
        center = (self._base_center[0] + shift[0], self._base_center[1] + shift[1])
        state = self._build(self.direction, anchor, center, points, targets)
        return MotionStep(state, "full" if full else "crossings", calls, changed)

