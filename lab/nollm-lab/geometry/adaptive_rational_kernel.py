"""Integer interval execution for the exact rational axial sample contract.

The retained ``certified_overlap.DyadicInterval`` supplies the independent
directed-arithmetic reference. That oracle serves ideal radical/area bounds
at 32--256 bits. This executor adapts its floor/ceiling rule to inexpensive
integer pairs, including 0/16 bits, and evaluates the existing rational maps.
It does not compute a nonlinear Fraction result before enclosing it.

At each requested precision every operation encloses the exact value. A target
is accepted only when its entire box is strictly within one hexagon, or the
box is an exact singleton classified by the original tie rule. Other samples
are recomputed at higher precision; only the final undecided ones use Fraction.
All scalar parameters retain their exact rational values. Precision controls
execution error, not the geometry, output shares, or persistent Core profile.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from fractions import Fraction
from math import lcm

from .rational_affine_kernel import (
    CompiledRationalAffine, compile_affine_pair, nearest_axial_ratio,
)
from .rational_geometry import RationalLayerMap, RationalRadialTwist, relative_layer_maps


Interval = tuple[int, int]
PointBox = tuple[Interval, Interval]
Cell = tuple[int, int]
Ratio = tuple[int, int]


def _ceil_ratio(numerator: int, denominator: int) -> int:
    return -((-numerator) // denominator)


def _add(a: Interval, b: Interval) -> Interval:
    return a[0] + b[0], a[1] + b[1]


def _sub(a: Interval, b: Interval) -> Interval:
    return a[0] - b[1], a[1] - b[0]


def _integer_multiple(a: Interval, n: int) -> Interval:
    return (a[0] * n, a[1] * n) if n >= 0 else (a[1] * n, a[0] * n)


def _rational_multiple(a: Interval, n: int, d: int) -> Interval:
    lo, hi = _integer_multiple(a, n)
    return lo // d, _ceil_ratio(hi, d)


@dataclass(frozen=True)
class _Dyadic:
    """Arithmetic context; accepted internal pairs share this positive scale."""

    scale: int

    def ratio(self, n: int, d: int) -> Interval:
        n *= self.scale
        return n // d, _ceil_ratio(n, d)

    def translate(self, a: Interval, n: int, d: int) -> Interval:
        offset = n * self.scale
        return (a[0] * d + offset) // d, _ceil_ratio(a[1] * d + offset, d)

    def multiply(self, a: Interval, b: Interval) -> Interval:
        products = a[0] * b[0], a[0] * b[1], a[1] * b[0], a[1] * b[1]
        return min(products) // self.scale, _ceil_ratio(max(products), self.scale)

    def square(self, a: Interval) -> Interval:
        ends = a[0] * a[0], a[1] * a[1]
        lower = 0 if a[0] <= 0 <= a[1] else min(ends)
        return lower // self.scale, _ceil_ratio(max(ends), self.scale)

    def divide_positive(self, a: Interval, b: Interval) -> Interval:
        # The sole caller constructs b = 1 + 3*square(t), hence b.lo >= scale.
        low_denominator = b[1] if a[0] >= 0 else b[0]
        high_denominator = b[0] if a[1] >= 0 else b[1]
        return (a[0] * self.scale // low_denominator,
                _ceil_ratio(a[1] * self.scale, high_denominator))


def _ratio(value: Fraction) -> Ratio:
    return value.numerator, value.denominator


def _affine_box(kernel: CompiledRationalAffine, point: PointBox, scale: int) -> PointBox:
    """Exact rational row coefficients applied to an existing dyadic box."""
    q, r = point

    def row(coefficients):
        a, b, c = coefficients
        lo, hi = _add(_integer_multiple(q, a), _integer_multiple(r, b))
        offset = c * scale
        return ((lo + offset) // kernel.denominator,
                _ceil_ratio(hi + offset, kernel.denominator))

    return row(kernel.q_row), row(kernel.r_row)


@dataclass(frozen=True)
class _Twist:
    center_q: Ratio
    center_r: Ratio
    radius_squared: Ratio
    strength: Ratio

    @classmethod
    def from_twist(cls, twist: RationalRadialTwist, sign: int) -> "_Twist":
        return cls(_ratio(twist.center[0]), _ratio(twist.center[1]),
                   _ratio(twist.radius_squared), _ratio(sign * twist.strength))

    def apply(self, point: PointBox, arithmetic: _Dyadic) -> PointBox:
        """Enclose the continuous global law k*max(1-N/R²,0)²."""
        q, r = point
        cq, cr = self.center_q, self.center_r
        u = arithmetic.translate(q, -cq[0], cq[1])
        v = arithmetic.translate(r, -cr[0], cr[1])
        u2, v2 = arithmetic.square(u), arithmetic.square(v)
        raw_norm = _add(_add(u2, v2), arithmetic.multiply(u, v))
        # Both N >= 0 and N >= (u²+v²)/2 hold in the axial metric. The latter
        # also recognizes distant boxes when uv's dependency bound is loose.
        norm = max(0, raw_norm[0], (u2[0] + v2[0]) // 2), raw_norm[1]
        radius_n, radius_d = self.radius_squared
        scale = arithmetic.scale
        if norm[0] * radius_d >= radius_n * scale:
            return point
        # Multiply by the exact positive reciprocal; even tiny positive R²
        # need not survive a preliminary quantization as a nonzero interval.
        normalized = _rational_multiple(norm, radius_d, radius_n)
        cutoff = max(0, scale - normalized[1]), max(0, scale - normalized[0])
        parameter = _rational_multiple(arithmetic.square(cutoff), *self.strength)
        if parameter == (0, 0):
            return point
        t2 = _integer_multiple(arithmetic.square(parameter), 3)
        denominator = scale + t2[0], scale + t2[1]
        middle = scale - t2[1], scale - t2[0]
        twice, four = _integer_multiple(parameter, 2), _integer_multiple(parameter, 4)
        first = _sub(arithmetic.multiply(_sub(middle, twice), u),
                     arithmetic.multiply(four, v))
        second = _add(arithmetic.multiply(four, u),
                      arithmetic.multiply(_add(middle, twice), v))
        moved_q = arithmetic.divide_positive(first, denominator)
        moved_r = arithmetic.divide_positive(second, denominator)
        return (arithmetic.translate(moved_q, *cq),
                arithmetic.translate(moved_r, *cr))


def certify_target_box(q_lo: int, q_hi: int, r_lo: int, r_hi: int,
                       scale: int) -> Cell | None:
    """Return a label valid for the entire supplied closed dyadic rectangle.

    The box endpoints and scale are the output of ``enclose_ratio``. Exact
    singleton ties keep absolute coordinates; translating by an odd integer
    would not preserve the existing half-even/cube-repair tie contract.
    """
    if scale <= 0 or q_lo > q_hi or r_lo > r_hi:
        raise ValueError("box requires ordered endpoints and positive scale")
    if q_lo == q_hi and r_lo == r_hi:
        return nearest_axial_ratio(q_lo, r_lo, scale)
    a, b = nearest_axial_ratio(q_lo + q_hi, r_lo + r_hi, 2 * scale)
    ulo, uhi = q_lo - a * scale, q_hi - a * scale
    vlo, vhi = r_lo - b * scale, r_hi - b * scale
    if (-scale < 2 * ulo + vlo and 2 * uhi + vhi < scale
            and -scale < ulo + 2 * vlo and uhi + 2 * vhi < scale
            and -scale < ulo - vhi and uhi - vlo < scale):
        return a, b
    return None


@dataclass(frozen=True)
class AdaptiveTargets:
    targets: tuple[Cell, ...]
    stats: dict


@dataclass(frozen=True)
class CompiledAdaptivePair:
    """Reusable geometry coefficients with request-local interval execution."""

    source_map: RationalLayerMap
    target_map: RationalLayerMap
    initial_bits: int
    max_bits: int
    cancelled_common_twists: int
    _source_kernel: CompiledRationalAffine | None
    _target_kernel: CompiledRationalAffine | None
    _affine_kernel: CompiledRationalAffine | None
    _twists: tuple[_Twist, ...]

    def _enclose_mapped(self, q: int, r: int, denominator: int, bits: int):
        arithmetic = _Dyadic(1 << bits)
        point = arithmetic.ratio(q, denominator), arithmetic.ratio(r, denominator)
        for twist in self._twists:
            point = twist.apply(point, arithmetic)
        (ql, qh), (rl, rh) = _affine_box(self._target_kernel, point, arithmetic.scale)
        return ql, qh, rl, rh, arithmetic.scale

    def enclose_ratio(self, q_num: int, r_num: int, denominator: int,
                      bits: int) -> tuple[int, int, int, int, int]:
        """Enclose target^-1(source((q_num,r_num)/denominator)) at p bits.

        Returns (q_lo,q_hi,r_lo,r_hi,2**bits). Coefficient preparation and the
        first affine evaluation use exact integer ratios, while every nonlinear
        step rounds its interval endpoints outward to the same dyadic scale.
        """
        if denominator <= 0 or bits < 0:
            raise ValueError("point denominator must be positive and bits nonnegative")
        if self._affine_kernel is not None:
            q, r, d = self._affine_kernel.map_ratio(q_num, r_num, denominator)
            arithmetic = _Dyadic(1 << bits)
            ql, qh = arithmetic.ratio(q, d)
            rl, rh = arithmetic.ratio(r, d)
            return ql, qh, rl, rh, arithmetic.scale
        q, r, d = self._source_kernel.map_ratio(q_num, r_num, denominator)
        return self._enclose_mapped(q, r, d, bits)

    def _exact_target(self, q_num: int, r_num: int, denominator: int) -> Cell:
        point = Fraction(q_num, denominator), Fraction(r_num, denominator)
        q, r = self.target_map.inverse(self.source_map.forward(point))
        common = lcm(q.denominator, r.denominator)
        return nearest_axial_ratio(q.numerator * (common // q.denominator),
                                   r.numerator * (common // r.denominator), common)

    def targets(self, q: int, r: int, offset_numerators: tuple[tuple[int, int], ...],
                offset_denominator: int) -> tuple[Cell, ...]:
        if self._affine_kernel is not None:
            return self._affine_kernel.targets(q, r, offset_numerators, offset_denominator)
        return self.targets_with_stats(q, r, offset_numerators, offset_denominator).targets

    def targets_with_stats(self, q: int, r: int,
                           offset_numerators: tuple[tuple[int, int], ...],
                           offset_denominator: int) -> AdaptiveTargets:
        """Classify each labeled sample, refining only undecided intervals.

        Stats count actual samples attempted/accepted at each bit setting and
        exact fallback work. They describe execution, not approximation error:
        all returned labels follow the existing exact rational contract.
        """
        if offset_denominator <= 0:
            raise ValueError("sample denominator must be positive")
        count = len(offset_numerators)
        stats = {"sample_count": count, "attempted_by_bits": {}, "certified_by_bits": {},
                 "exact_fallback": 0, "affine_exact": 0,
                 "cancelled_common_twists": self.cancelled_common_twists}
        if self._affine_kernel is not None:
            stats["affine_exact"] = count
            return AdaptiveTargets(self._affine_kernel.targets(
                q, r, offset_numerators, offset_denominator), stats)
        points = tuple((q * offset_denominator + dq, r * offset_denominator + dr)
                       for dq, dr in offset_numerators)
        # Exact integer affine preparation once per labeled sample, reused at
        # every precision. No huge local integer is multiplied by a rounded
        # matrix coefficient, and no nonlinear Fraction is evaluated here.
        mapped = tuple(self._source_kernel.map_ratio(a, b, offset_denominator)
                       for a, b in points)
        labels = [None] * count
        pending = list(range(count))
        bits = self.initial_bits
        while pending:
            stats["attempted_by_bits"][bits] = len(pending)
            unresolved = []
            for index in pending:
                target = certify_target_box(*self._enclose_mapped(*mapped[index], bits))
                if target is None:
                    unresolved.append(index)
                else:
                    labels[index] = target
            stats["certified_by_bits"][bits] = len(pending) - len(unresolved)
            pending = unresolved
            if bits == self.max_bits:
                break
            bits = min(self.max_bits, max(bits + 1, 2 * bits))
        for index in pending:
            labels[index] = self._exact_target(*points[index], offset_denominator)
        stats["exact_fallback"] = len(pending)
        return AdaptiveTargets(tuple(labels), stats)


def compile_adaptive_pair(source_map: RationalLayerMap, target_map: RationalLayerMap,
                          *, initial_bits: int = 16, max_bits: int = 128) -> CompiledAdaptivePair:
    """Prepare an exact-equivalent execution strategy for a pair of Lab maps.

    Only identical ordered outer suffixes cancel. No approximate equality or
    commutation is used. Common world translation is then removed exactly,
    including all remaining twist centers. Pure affine work keeps the existing
    exact integer kernel; otherwise bits rise from initial_bits to max_bits
    before exact handling of any remaining sample. ``max_bits`` limits interval
    refinement, not the precision of that final exact fallback.
    """
    if initial_bits < 0 or max_bits < initial_bits:
        raise ValueError("precision requires 0 <= initial_bits <= max_bits")
    affine = compile_affine_pair(source_map, target_map)
    if affine is not None:
        # The existing compiler already cancels the complete common twist
        # sequence and world translation. This path needs no interval frames.
        return CompiledAdaptivePair(
            source_map, target_map, initial_bits, max_bits, len(source_map.twists),
            None, None, affine, (),
        )
    source_twists, target_twists = source_map.twists, target_map.twists
    cancelled = 0
    while (cancelled < min(len(source_twists), len(target_twists))
           and source_twists[-1-cancelled] == target_twists[-1-cancelled]):
        cancelled += 1
    if cancelled:
        source_map = replace(source_map, twists=source_twists[:-cancelled])
        target_map = replace(target_map, twists=target_twists[:-cancelled])
    source_map, target_map = relative_layer_maps(source_map, target_map)
    affine = compile_affine_pair(source_map, target_map)
    twists = tuple(_Twist.from_twist(twist, sign)
                   for sequence, sign in ((source_map.twists, 1),
                                          (reversed(target_map.twists), -1))
                   for twist in sequence if twist.strength != 0)
    return CompiledAdaptivePair(
        source_map, target_map, initial_bits, max_bits, cancelled,
        CompiledRationalAffine.from_frame(source_map.frame),
        CompiledRationalAffine.from_frame(target_map.frame.inverse_frame()), affine, twists,
    )
