"""Exact reuse of the current Q40 sample footprint under translation.

This Lab component evaluates hypothetical motion, without changing Core state
or its fixed geometry contract. It preserves the original nearest-cell tie
rule and Q16 normalization. Raw target coordinates are diagnostic; a caller
that persists cells must still apply the storage domain's admission rules.
"""
from __future__ import annotations

from bisect import bisect_left, bisect_right
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
# This is a one-step residual-distance cost gate, not a correctness bound.
# Both paths produce the same exact result, including after accumulated motion.
REBUILD_DISTANCE_Q40 = Q40_ONE // 16
_ORIGIN = GeometryAddress("default_dream_v1", "default", 0, 0, 0)


def _margins(point: Point, target: Point) -> tuple[int, ...]:
    q = point[0] - Q40_ONE * target[0]
    r = point[1] - Q40_ONE * target[1]
    a, b, c = 2 * q + r, q + 2 * r, r - q
    return (Q40_ONE - a, Q40_ONE - b, Q40_ONE - c,
            Q40_ONE + a, Q40_ONE + b, Q40_ONE + c)


def _counts(targets: tuple[Point, ...]) -> tuple[tuple[int, int, int, int], ...]:
    return _count_records(Counter(targets))


def _count_records(counts) -> tuple[tuple[int, int, int, int], ...]:
    counts = sorted(counts.items())
    weights = normalize_q16_weights([count for _, count in counts])
    return tuple((q, r, count, weight)
                 for ((q, r), count), weight in zip(counts, weights))


def _split_even(delta: int) -> tuple[int, int]:
    block, residual = divmod(delta + Q40_ONE, 2 * Q40_ONE)
    return 2 * block, residual - Q40_ONE


@dataclass(frozen=True)
class _ProjectionEvents:
    """Sorted immutable point projections, retaining every sample's label."""

    values: tuple[int, ...]
    prefixes: tuple[int, ...]
    rank_bits: tuple[int, ...]


def _projection_events(points):
    events = []
    for hq, hr in NORMALS[:3]:
        ordered = sorted((hq * q + hr * r, i) for i, (q, r) in enumerate(points))
        prefixes = [0]
        rank_bits = [0] * len(points)
        for rank, (_, i) in enumerate(ordered):
            prefixes.append(prefixes[-1] | (1 << i))
            rank_bits[i] = 1 << rank
        events.append(_ProjectionEvents(tuple(value for value, _ in ordered),
                                        tuple(prefixes), tuple(rank_bits)))
    return tuple(events)


def _projection_groups(targets, events):
    """Group only a face test's equal integer offsets, not source identities.

    Each value is (original-sample mask, projection-rank mask). The latter gives
    the group's minimum/maximum projection without scanning its members.
    """
    groups = []
    for (hq, hr), event in zip(NORMALS[:3], events):
        grouped = {}
        for i, (q, r) in enumerate(targets):
            key = hq * q + hr * r
            samples, ranks = grouped.get(key, (0, 0))
            grouped[key] = samples | (1 << i), ranks | event.rank_bits[i]
        groups.append(grouped)
    return tuple(groups)


def _group_minima(groups, events):
    positive, negative = [], []
    for grouped, event in zip(groups, events):
        positive.append(min(Q40_ONE * (key + 1) - event.values[ranks.bit_length() - 1]
                            for key, (_, ranks) in grouped.items()))
        negative.append(min(Q40_ONE * (1 - key)
                            + event.values[(ranks & -ranks).bit_length() - 1]
                            for key, (_, ranks) in grouped.items()))
    return tuple(positive + negative)


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
    update 96 point arrays. Sorted projections represent all six faces using
    three normals and two inclusive tails. On crossings, only changed sample
    labels move between target-projection groups; the point phases and sorted
    arrays stay shared; they are built lazily at the first small crossing.
    This disposable certificate describes sample geometry only.
    """

    direction: str
    anchor: Point
    _base_center: Point
    _points: tuple[Point, ...]
    _targets: tuple[Point, ...]
    _margins: tuple[tuple[int, ...], ...]
    _minima: tuple[int, ...]
    _counts_q16: tuple[tuple[int, int, int, int], ...]
    _events: tuple[_ProjectionEvents, ...] | None
    _groups: tuple[dict[int, tuple[int, int]], ...] | None
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
    def _build(cls, direction, anchor, center, points, targets, *, events=None, shift=(0, 0)):
        margins = tuple(_margins(point, target) for point, target in zip(points, targets))
        groups = _projection_groups(targets, events) if events is not None else None
        minima = (_group_minima(groups, events) if groups is not None else
                  tuple(min(row[i] for row in margins) for i in range(6)))
        return cls(direction, anchor, center, points, targets, margins,
                   minima, _counts(targets), events, groups, shift)

    def _at(self, anchor, shift):
        # This hot, position-only copy shares every certificate array. A direct
        # constructor avoids field-name reflection in dataclasses.replace.
        return TranslationFootprint(self.direction, anchor, self._base_center,
                                    self._points, self._targets, self._margins,
                                    self._minima, self._counts_q16,
                                    self._events, self._groups, shift)

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
        changes, and rebuilds target membership on large changes. ``full``
        recomputes every point and serves as a direct comparison path. Only
        even whole-cell shifts are factored out; an odd-cell shift still uses
        the original tie rule.
        """
        if mode not in {"auto", "full"}:
            raise ValueError("mode must be auto or full")
        aq, dq = _split_even(delta_q40[0])
        ar, dr = _split_even(delta_q40[1])
        anchor = (self.anchor[0] + aq, self.anchor[1] + ar)
        shift = (self._shift[0] + dq, self._shift[1] + dr)
        if mode == "auto" and (dq, dr) == (0, 0):
            state = self if anchor == self.anchor else self._at(anchor, self._shift)
            return MotionStep(state, "reuse", 0, len(self._targets) if (aq or ar) else 0)

        projections = tuple(hq * shift[0] + hr * shift[1] for hq, hr in NORMALS)
        if mode == "auto" and all(p < m for p, m in zip(projections, self._minima)):
            return MotionStep(self._at(anchor, shift), "reuse", 0,
                              len(self._targets) if (aq or ar) else 0)

        distance = max(abs(dq), abs(dr), abs(dq + dr))
        full = mode == "full" or distance >= REBUILD_DISTANCE_Q40
        if full:
            targets = tuple(nearest_axial_q40(q + shift[0], r + shift[1])
                            for q, r in self._points)
            changed = sum((q + aq, r + ar) != old
                          for (q, r), old in zip(targets, self._targets))
            state = self._build(self.direction, anchor, self._base_center,
                                self._points, targets, events=self._events, shift=shift)
            return MotionStep(state, "full", len(targets), changed)

        # Every point outside a strict six-face interior is an exact residual.
        # Both equalities are included: only the original rounder resolves ties.
        # Delay sorting until the first small crossing. A safe-only trajectory
        # or a one-off large jump does not benefit from constructing the index.
        events = self._events
        groups = self._groups
        if events is None:
            events = _projection_events(self._points)
            groups = _projection_groups(self._targets, events)
        residual = 0
        for projection, event, grouped in zip(projections, events, groups):
            for key, (samples, _) in grouped.items():
                lower = bisect_right(event.values, Q40_ONE * (key - 1) - projection)
                upper = bisect_left(event.values, Q40_ONE * (key + 1) - projection)
                residual |= samples & (event.prefixes[lower]
                                       | (event.prefixes[-1] ^ event.prefixes[upper]))
        calls = residual.bit_count()
        updated = list(self._targets)
        margins = list(self._margins)
        groups = tuple(dict(grouped) for grouped in groups)
        counts = {(q, r): count for q, r, count, _ in self._counts_q16}
        changed = len(updated) if (aq or ar) else 0
        relabeled = False
        while residual:
            bit = residual & -residual
            residual ^= bit
            i = bit.bit_length() - 1
            q, r = self._points[i]
            target = nearest_axial_q40(q + shift[0], r + shift[1])
            old = self._targets[i]
            if target == old:
                continue
            relabeled = True
            updated[i] = target
            margins[i] = _margins(self._points[i], target)
            counts[old] -= 1
            if not counts[old]:
                del counts[old]
            counts[target] = counts.get(target, 0) + 1
            changed += int((target[0] + aq, target[1] + ar) != old) - int(bool(aq or ar))
            for (hq, hr), event, grouped in zip(NORMALS[:3], events, groups):
                old_key = hq * old[0] + hr * old[1]
                new_key = hq * target[0] + hr * target[1]
                if old_key == new_key:
                    continue
                rank_bit = event.rank_bits[i]
                samples, ranks = grouped[old_key]
                if samples == bit:
                    del grouped[old_key]
                else:
                    grouped[old_key] = samples ^ bit, ranks ^ rank_bit
                samples, ranks = grouped.get(new_key, (0, 0))
                grouped[new_key] = samples | bit, ranks | rank_bit
        if relabeled:
            state = replace(self, anchor=anchor, _shift=shift, _targets=tuple(updated),
                            _margins=tuple(margins), _events=events, _groups=groups,
                            _minima=_group_minima(groups, events),
                            _counts_q16=_count_records(counts))
        else:
            state = replace(self, anchor=anchor, _shift=shift, _events=events, _groups=groups)
        return MotionStep(state, "crossings", calls, changed)

