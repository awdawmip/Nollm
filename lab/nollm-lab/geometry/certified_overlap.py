"""Lab-only enclosures of ideal adjacent-layer hex overlap.

No rounded Q40 constants, samples, trigonometric approximations or Core imports
are used. Integer outward-rounded radicals enclose the ideal transform; exact
rational inner/outer half-plane clips enclose source-area shares. The proof and
scope are in CERTIFIED_OVERLAP.md. This is not a production kernel replacement.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F
from functools import lru_cache
from math import isqrt

METHOD = "ideal_hex_radical_halfplane_enclosure_v1"
RADIUS = (1 << 31) - 1
NORMALS = ((2, 1), (1, 2), (-1, 1), (-2, -1), (-1, -2), (1, -1))
HEX = tuple((F(q, 3), F(r, 3)) for q, r in
            ((1, 1), (-1, 2), (-2, 1), (-1, -1), (1, -2), (2, -1)))
Point = tuple[F, F]


class CertificationBudgetExceeded(ValueError):
    """A bounded calculation could not achieve the requested certificate."""


def _integer(value: object, name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer")
    return value


def _ceil_ratio(a: int, b: int) -> int:
    return -((-a) // b)


@dataclass(frozen=True)
class DyadicInterval:
    """Closed [lo/2**bits, hi/2**bits], with directed integer arithmetic."""
    lo: int
    hi: int
    bits: int

    def __post_init__(self) -> None:
        for name in ("lo", "hi", "bits"):
            _integer(getattr(self, name), name)
        if not 32 <= self.bits <= 256 or self.lo > self.hi:
            raise ValueError("invalid interval or precision outside [32,256]")

    @classmethod
    def integer(cls, n: int, bits: int) -> DyadicInterval:
        _integer(n, "n")
        _integer(bits, "bits")
        if not 32 <= bits <= 256:
            raise ValueError("precision outside [32,256]")
        return cls(n << bits, n << bits, bits)

    def _other(self, value: object) -> DyadicInterval:
        if type(value) is int:
            return self.integer(value, self.bits)
        if type(value) is not DyadicInterval or value.bits != self.bits:
            raise TypeError("interval operands require the same precision")
        return value

    def __add__(self, other: object) -> DyadicInterval:
        b = self._other(other)
        return type(self)(self.lo + b.lo, self.hi + b.hi, self.bits)

    __radd__ = __add__

    def __neg__(self) -> DyadicInterval:
        return type(self)(-self.hi, -self.lo, self.bits)

    def __sub__(self, other: object) -> DyadicInterval:
        return self + -self._other(other)

    def __rsub__(self, other: object) -> DyadicInterval:
        return self._other(other) + -self

    def __mul__(self, other: object) -> DyadicInterval:
        b = self._other(other)
        products = (self.lo*b.lo, self.lo*b.hi, self.hi*b.lo, self.hi*b.hi)
        s = 1 << self.bits
        return type(self)(min(products)//s, _ceil_ratio(max(products), s), self.bits)

    __rmul__ = __mul__

    def reciprocal(self) -> DyadicInterval:
        if self.lo <= 0 <= self.hi:
            raise ZeroDivisionError("interval contains zero")
        s2 = 1 << (2*self.bits)
        return type(self)(s2//self.hi, _ceil_ratio(s2, self.lo), self.bits)

    def __truediv__(self, other: object) -> DyadicInterval:
        return self * self._other(other).reciprocal()

    def sqrt(self) -> DyadicInterval:
        if self.lo < 0:
            raise ValueError("square root requires a nonnegative interval")
        a, b = self.lo << self.bits, self.hi << self.bits
        lower, upper = isqrt(a), isqrt(b)
        return type(self)(lower, upper + (upper*upper < b), self.bits)

    @property
    def lower(self) -> F:
        return F(self.lo, 1 << self.bits)

    @property
    def upper(self) -> F:
        return F(self.hi, 1 << self.bits)

    @property
    def midpoint(self) -> F:
        return F(self.lo + self.hi, 2 << self.bits)

    @property
    def radius(self) -> F:
        return F(self.hi - self.lo, 2 << self.bits)


def ideal_transform(direction: str, bits: int = 96) -> tuple[DyadicInterval, ...]:
    """Enclose T=scale B^-1 R(angle) B; row-major target axial coordinates.

    down: scale=2**(1/4), angle=-pi/8; up is its inverse.
    This uses the existing Decimal oracle's unwrapped relative chart convention.
    """
    if type(direction) is not str or direction not in ("coverage_up", "coverage_down"):
        raise ValueError("direction must be coverage_up or coverage_down")
    _integer(bits, "bits")
    if not 32 <= bits <= 256:
        raise ValueError("precision outside [32,256]")
    return _ideal_transform_cached(direction, bits)


@lru_cache(maxsize=16)
def _ideal_transform_cached(direction: str, bits: int) -> tuple[DyadicInterval, ...]:
    two = DyadicInterval.integer(2, bits)
    sqrt2 = two.sqrt()
    beta = sqrt2.sqrt()
    cosine = (two + sqrt2).sqrt() / 2
    sine = (two - sqrt2).sqrt() / 2
    t = sine / DyadicInterval.integer(3, bits).sqrt()
    if direction == "coverage_down":
        return (beta*(cosine+t), beta*(2*t), beta*(-2*t), beta*(cosine-t))
    scale = beta.reciprocal()
    return (scale*(cosine-t), scale*(-2*t), scale*(2*t), scale*(cosine+t))


def clip_halfplane(poly: tuple[Point, ...], a: F, b: F, c: F) -> tuple[Point, ...]:
    """Exact convex clip by a*x+b*y<=c. Boundary points are retained."""
    if not poly:
        return ()
    output = []
    previous = poly[-1]
    fp = a*previous[0] + b*previous[1] - c
    for current in poly:
        fc = a*current[0] + b*current[1] - c
        if (fp > 0) != (fc > 0):
            # Opposite classifications imply fp-fc != 0; no epsilon fallback.
            t = fp/(fp-fc)
            output.append((previous[0]+t*(current[0]-previous[0]),
                           previous[1]+t*(current[1]-previous[1])))
        if fc <= 0:
            output.append(current)
        previous, fp = current, fc
    return tuple(output)


def area(poly: tuple[Point, ...]) -> F:
    if len(poly) < 3:
        return F(0)
    return abs(sum((p[0]*q[1]-p[1]*q[0] for p, q in
                    zip(poly, poly[1:]+poly[:1])), F(0)))/2


@dataclass(frozen=True)
class OverlapMember:
    q: int
    r: int
    lower: F
    upper: F

    @property
    def classification(self) -> str:
        return "positive" if self.lower > 0 else "unresolved"


@dataclass(frozen=True)
class CoverageEnclosure:
    source_layer: int
    q: int
    r: int
    direction: str
    precision_bits: int
    candidate_count: int
    members: tuple[OverlapMember, ...]

    @property
    def total_lower(self) -> F:
        return sum((m.lower for m in self.members), F(0))

    @property
    def total_upper(self) -> F:
        return sum((m.upper for m in self.members), F(0))

    @property
    def total_width(self) -> F:
        return self.total_upper-self.total_lower

    def shares(self) -> dict[tuple[int, int], tuple[F, F]]:
        return {(m.q, m.r): (m.lower, m.upper) for m in self.members}

    def compare_q16(self, weights: dict[tuple[int, int], int]) -> dict[str, tuple[F, F]]:
        """Rigorous per-request errors against normalized production Q16 weights.

        Preserve target identities until after absolute differences are formed.
        Missing targets are zero in the estimate, not zero in physical geometry.
        """
        if type(weights) is not dict or not weights:
            raise TypeError("weights must be a nonempty target-to-Q16 dictionary")
        for key, value in weights.items():
            if type(key) is not tuple or len(key) != 2 or any(type(x) is not int for x in key):
                raise TypeError("weight keys must be integer (q,r) pairs")
            if type(value) is not int or not 0 <= value <= 65536:
                raise ValueError("weights must be Q16 integers in [0,65536]")
        if sum(weights.values()) != 65536:
            raise ValueError("weights must sum to 65536")
        shares = self.shares()
        tv_lo = tv_hi = missed_lo = missed_hi = F(0)
        for key in sorted(shares.keys() | weights.keys()):
            lo, hi = shares.get(key, (F(0), F(0)))
            w = F(weights.get(key, 0), 65536)
            tv_lo += max(F(0), lo-w, w-hi)
            tv_hi += max(abs(w-lo), abs(w-hi))
            if w == 0:
                missed_lo += lo
                missed_hi += hi
        return {"total_variation": (tv_lo/2, min(F(1), tv_hi/2)),
                "missed_mass": (missed_lo, min(F(1), missed_hi))}


def _validate(layer: int, q: int, r: int, direction: str, max_candidates: int) -> None:
    for name, value in (("layer", layer), ("q", q), ("r", r), ("max_candidates", max_candidates)):
        _integer(value, name)
    if type(direction) is not str or direction not in ("coverage_up", "coverage_down"):
        raise ValueError("direction must be coverage_up or coverage_down")
    target = layer + (1 if direction == "coverage_down" else -1)
    if not -64 <= layer <= 64 or not -64 <= target <= 64:
        raise ValueError("adjacent layers must lie in [-64,64]")
    if max(abs(q), abs(r), abs(q+r)) > RADIUS:
        raise ValueError("source outside signed-31 hex radius")
    if not 1 <= max_candidates <= 256:
        raise ValueError("max_candidates must lie in [1,256]")


def coverage_enclosure(layer: int, q: int, r: int, direction: str, *,
                       bits: int = 96, max_candidates: int = 64) -> CoverageEnclosure:
    """Enclose every positive-area ideal target share, including tiny slivers.

    The source H has area one in axial coordinates and |x|,|y|<=2/3.
    If n=(q,r), overlap with target k is H intersect all
    h*T*x <= 1+h*k-h*T*n, for the six hex normals h.
    Matrix uncertainty gives a uniform half-plane error E over H. Clipping
    nominal inequalities with rhs-E and rhs+E gives inner/outer regions.
    All arithmetic after radical enclosure is exact rational arithmetic.
    """
    _validate(layer, q, r, direction, max_candidates)
    transform = ideal_transform(direction, bits)
    center = (q*transform[0]+r*transform[1], q*transform[2]+r*transform[3])
    ranges = []
    for i in (0, 1):
        row = transform[2*i:2*i+2]
        reach = F(2, 3)*(1+sum(max(abs(v.lower), abs(v.upper)) for v in row))
        low, high = center[i].lower-reach, center[i].upper+reach
        ranges.append(range(_ceil_ratio(low.numerator, low.denominator), high.numerator//high.denominator+1))
    count = len(ranges[0])*len(ranges[1])
    if count > max_candidates:
        raise CertificationBudgetExceeded(f"candidate count {count} exceeds {max_candidates}")

    planes = []
    for hq, hr in NORMALS:
        a = hq*transform[0]+hr*transform[2]
        b = hq*transform[1]+hr*transform[3]
        d = q*a+r*b
        error = d.radius + F(2, 3)*(a.radius+b.radius)
        planes.append((hq, hr, a.midpoint, b.midpoint, d.midpoint, error))
    members = []
    for tq in ranges[0]:
        for tr in ranges[1]:
            inner = outer = HEX
            for hq, hr, a, b, d, error in planes:
                rhs = 1+hq*tq+hr*tr-d
                inner = clip_halfplane(inner, a, b, rhs-error)
                outer = clip_halfplane(outer, a, b, rhs+error)
            lo, hi = area(inner), min(F(1), area(outer))
            if not 0 <= lo <= hi <= 1:
                raise ArithmeticError("invalid geometric enclosure")
            if hi > 0:
                members.append(OverlapMember(tq, tr, lo, hi))
    result = CoverageEnclosure(layer, q, r, direction, bits, count, tuple(members))
    if not result.total_lower <= 1 <= result.total_upper:
        raise ArithmeticError("candidate completeness / partition enclosure failed")
    return result


def certify_coverage(layer: int, q: int, r: int, direction: str, *,
                     tolerance: F = F(1, 1 << 64), max_bits: int = 192,
                     max_candidates: int = 64) -> CoverageEnclosure:
    """Bounded refinement; unresolved support is never silently excluded.

    Width tolerance is the sum of source-share interval widths, not a bound on
    the old 96-sample algorithm's error and not a claim of exact support.
    """
    if type(tolerance) is not F or not 0 < tolerance < 1:
        raise ValueError("tolerance must be a Fraction strictly between zero and one")
    _integer(max_bits, "max_bits")
    if not 64 <= max_bits <= 256:
        raise ValueError("max_bits must lie in [64,256]")
    precisions = sorted(set([p for p in (64, 96, 128, 160, 192, 224, 256) if p <= max_bits]+[max_bits]))
    for bits in precisions:
        result = coverage_enclosure(layer, q, r, direction, bits=bits, max_candidates=max_candidates)
        if result.total_width <= tolerance:
            return result
    raise CertificationBudgetExceeded("requested area width not certified within precision budget")
