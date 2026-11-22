"""Compile an exact rational relative affine map into integer arithmetic.

The six affine coefficients share one positive denominator. Rational point
coordinates share another; a sample then needs only integer multiply/add and
the original half-even/cube tie ordering, without intermediate quantization.
Compilation is reusable geometry state, not a relation or object index.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import lcm

from .rational_geometry import RationalAffine, RationalLayerMap


def _round_ratio(numerator: int, denominator: int) -> int:
    sign = -1 if numerator < 0 else 1
    whole, remainder = divmod(abs(numerator), denominator)
    if 2*remainder > denominator or (2*remainder == denominator and whole % 2):
        whole += 1
    return sign*whole


def nearest_axial_ratio(q: int, r: int, denominator: int) -> tuple[int, int]:
    """Classify exact (q/denominator,r/denominator); no Q40 projection."""
    if denominator <= 0:
        raise ValueError("coordinate denominator must be positive")
    x, z, y = (_round_ratio(value, denominator) for value in (q, r, -q-r))
    dx, dz, dy = (abs(x*denominator-q), abs(z*denominator-r),
                  abs(y*denominator+q+r))
    if dx >= dz and dx >= dy:
        x = -y-z
    elif dz >= dy:
        z = -x-y
    return x, z


@dataclass(frozen=True)
class CompiledRationalAffine:
    """Rows (a,b,c) mean output=(a*q+b*r+c)/denominator."""

    q_row: tuple[int, int, int]
    r_row: tuple[int, int, int]
    denominator: int

    @classmethod
    def from_frame(cls, frame: RationalAffine) -> "CompiledRationalAffine":
        offset = frame.forward((0, 0))
        coefficients = (*frame.matrix[0], offset[0], *frame.matrix[1], offset[1])
        divisor = lcm(*(value.denominator for value in coefficients))
        integers = tuple(value.numerator*(divisor//value.denominator)
                         for value in coefficients)
        return cls(integers[:3], integers[3:], divisor)

    def map_ratio(self, q: int, r: int, point_denominator: int = 1) -> tuple[int, int, int]:
        if point_denominator <= 0:
            raise ValueError("point denominator must be positive")
        a, b, c = self.q_row
        d, e, f = self.r_row
        return (a*q+b*r+c*point_denominator, d*q+e*r+f*point_denominator,
                self.denominator*point_denominator)

    def targets(self, q: int, r: int, offset_numerators: tuple[tuple[int, int], ...],
                offset_denominator: int) -> tuple[tuple[int, int], ...]:
        """Classify a full labeled stencil around the integer source cell."""
        if offset_denominator <= 0:
            raise ValueError("sample denominator must be positive")
        a, b, c = self.q_row
        d, e, f = self.r_row
        base_q = offset_denominator*(a*q+b*r+c)
        base_r = offset_denominator*(d*q+e*r+f)
        divisor = self.denominator*offset_denominator
        return tuple(nearest_axial_ratio(base_q+a*dq+b*dr, base_r+d*dq+e*dr, divisor)
                     for dq, dr in offset_numerators)


def compile_affine_pair(source_map: RationalLayerMap,
                        target_map: RationalLayerMap) -> CompiledRationalAffine | None:
    """Compile target^-1(source(point)) when its common outer twists cancel.

    If both maps have the same ordered world twists W, their exact relative
    map is (W A_t)^-1(W A_s)=A_t^-1 A_s. The rational maps have analytic exact
    inverses, so cancellation is valid here even though it is not a bitwise
    identity for the old float64 execution. Other twist pairs use the full
    rational path; no approximate equality or commutation is assumed.
    """
    if source_map.twists != target_map.twists:
        return None
    relative = target_map.frame.inverse_frame().after(source_map.frame)
    return CompiledRationalAffine.from_frame(relative)
