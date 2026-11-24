"""Cell-local, one-pass fixed-point execution of explicit rational Lab maps.

The caller declares the source layer's positive rational cell length in world units.
For source cell c the world anchor is its exact pre-twist affine position A_s(c).
Both frames and all remaining twists are expressed in (world - A_s(c))/length.
Representation-only reanchoring and a common change of world units therefore
leave the normalized coefficients unchanged. Eight fractional bits are the
default; accepted sample labels define this distinct numerical contract.

Whole target addresses stay exact. An even integer target anchor is removed
before the final rounding and restored after cube classification, preserving
the existing signed half-even boundary rule. Pair compilation uses Fraction;
cell preparation and all sample operations use integer coefficients. Pure
affine pairs continue through the established exact integer evaluator.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from fractions import Fraction
from functools import lru_cache
from math import lcm

from .quantized_rational_kernel import _QuantizedTwist
from .rational_affine_kernel import (
    CompiledRationalAffine, _round_ratio, compile_affine_pair, nearest_axial_ratio,
)
from .rational_geometry import Q, RationalAffine, RationalLayerMap


LOCAL_QUANTIZED_CONTRACT_ID = "lab_local_quantized_rational_axial_quadrature_v1"


@lru_cache(maxsize=128)
def _source_stencil(kernel, fractional_bits, offsets, denominator):
    """Every cell has the same normalized source offsets; cache only geometry."""
    scale = 1 << fractional_bits
    result = []
    for q, r in offsets:
        q, r, divisor = kernel.map_ratio(q, r, denominator)
        result.append((_round_ratio(q * scale, divisor), _round_ratio(r * scale, divisor)))
    return tuple(result)


@dataclass(frozen=True)
class _LocalTwist:
    center: CompiledRationalAffine
    radius: Fraction
    strength: Fraction

    def for_cell(self, q: int, r: int, scale: int) -> _QuantizedTwist:
        cq, cr, denominator = self.center.map_ratio(q, r)
        return _QuantizedTwist(
            _round_ratio(cq * scale, denominator), _round_ratio(cr * scale, denominator),
            self.radius.numerator, self.radius.denominator,
            self.strength.numerator, self.strength.denominator,
        )


@dataclass(frozen=True)
class LocalQuantizedCell:
    """One source cell fixes one quantization phase for its complete stencil."""

    fractional_bits: int
    source_cell: tuple[int, int]
    target_anchor: tuple[int, int]
    _source_kernel: CompiledRationalAffine | None
    _target_kernel: CompiledRationalAffine | None
    _affine_kernel: CompiledRationalAffine | None
    _twists: tuple[_QuantizedTwist, ...]

    def _local_ratio(self, q_num: int, r_num: int, denominator: int):
        scale = 1 << self.fractional_bits
        q, r, divisor = self._source_kernel.map_ratio(q_num, r_num, denominator)
        q, r = _round_ratio(q * scale, divisor), _round_ratio(r * scale, divisor)
        return self._map_fixed(q, r)

    def _map_fixed(self, q: int, r: int):
        scale = 1 << self.fractional_bits
        for twist in self._twists:
            q, r = twist.apply(q, r, scale)
        q, r, divisor = self._target_kernel.map_ratio(q, r, scale)
        return _round_ratio(q * scale, divisor), _round_ratio(r * scale, divisor), scale

    def map_offset_ratio(self, q_num: int, r_num: int, denominator: int = 1):
        """Map an offset from this cell; return full integer numerators/divisor."""
        if self._affine_kernel is not None:
            q, r = self.source_cell
            return self._affine_kernel.map_ratio(q * denominator + q_num,
                                                 r * denominator + r_num, denominator)
        q, r, scale = self._local_ratio(q_num, r_num, denominator)
        aq, ar = self.target_anchor
        return aq * scale + q, ar * scale + r, scale

    def targets(self, offsets: tuple[tuple[int, int], ...], denominator: int):
        if self._affine_kernel is not None:
            return self._affine_kernel.targets(*self.source_cell, offsets, denominator)
        aq, ar = self.target_anchor
        result = []
        for q, r in _source_stencil(self._source_kernel, self.fractional_bits, offsets, denominator):
            tq, tr = nearest_axial_ratio(*self._map_fixed(q, r))
            result.append((aq + tq, ar + tr))
        return tuple(result)


@dataclass(frozen=True)
class CompiledLocalQuantizedPair:
    fractional_bits: int
    local_length: Fraction
    cancelled_common_twists: int
    _source_kernel: CompiledRationalAffine | None
    _target_linear: CompiledRationalAffine | None
    _target_centers: CompiledRationalAffine | None
    _affine_kernel: CompiledRationalAffine | None
    _twists: tuple[_LocalTwist, ...]

    @property
    def execution_kind(self):
        return "integer_affine" if self._affine_kernel is not None else "local_fixed_point_nonlinear"

    def for_cell(self, q: int, r: int) -> LocalQuantizedCell:
        if self._affine_kernel is not None:
            return LocalQuantizedCell(self.fractional_bits, (q, r), (0, 0),
                                      None, None, self._affine_kernel, ())
        # T=A_t^-1(A_s(c)) is evaluated before any rounding, at the full address.
        tq, tr, td = self._target_centers.map_ratio(q, r)
        aq, ar = 2 * (tq // (2 * td)), 2 * (tr // (2 * td))
        linear = self._target_linear
        divisor = lcm(td, linear.denominator)
        matrix_factor, offset_factor = divisor // linear.denominator, divisor // td
        target = CompiledRationalAffine(
            (linear.q_row[0] * matrix_factor, linear.q_row[1] * matrix_factor,
             (tq - aq * td) * offset_factor),
            (linear.r_row[0] * matrix_factor, linear.r_row[1] * matrix_factor,
             (tr - ar * td) * offset_factor), divisor,
        )
        scale = 1 << self.fractional_bits
        return LocalQuantizedCell(self.fractional_bits, (q, r), (aq, ar),
                                  self._source_kernel, target, None,
                                  tuple(twist.for_cell(q, r, scale) for twist in self._twists))

    def targets(self, q: int, r: int, offset_numerators: tuple[tuple[int, int], ...],
                offset_denominator: int):
        if offset_denominator <= 0:
            raise ValueError("sample denominator must be positive")
        return self.for_cell(q, r).targets(offset_numerators, offset_denominator)


def compile_local_quantized_pair(source_map: RationalLayerMap, target_map: RationalLayerMap,
                                 *, local_length, fractional_bits: int = 8):
    """Compile an adjacent-pair evaluator with an explicit source-cell unit.

    ``local_length`` is the source layer's declared positive rational world
    length. A common world scaling by lambda also scales this value by lambda.
    General affine maps can supply their declared unit without extracting an
    irrational square root or mistaking shear for a radial similarity.
    Adjacency and address-domain checks belong to the public coverage API.
    """
    length = Q(local_length)
    if length <= 0:
        raise ValueError("local_length must be positive")
    if not isinstance(fractional_bits, int) or fractional_bits < 0:
        raise ValueError("fractional bits must be a nonnegative integer")
    # Identity operations must not hide an otherwise cancellable outer suffix.
    source_map = replace(source_map, twists=tuple(t for t in source_map.twists if t.strength))
    target_map = replace(target_map, twists=tuple(t for t in target_map.twists if t.strength))
    source_twists, target_twists = source_map.twists, target_map.twists
    cancelled = 0
    while (cancelled < min(len(source_twists), len(target_twists))
           and source_twists[-1-cancelled] == target_twists[-1-cancelled]):
        cancelled += 1
    if cancelled:
        source_map = replace(source_map, twists=source_twists[:-cancelled])
        target_map = replace(target_map, twists=target_twists[:-cancelled])
    affine = compile_affine_pair(source_map, target_map)
    if affine is not None:
        return CompiledLocalQuantizedPair(fractional_bits, length, cancelled,
                                          None, None, None, affine, ())
    source_matrix = tuple(tuple(value / length for value in row)
                          for row in source_map.frame.matrix)
    source_origin = source_map.frame.forward((0, 0))
    inverse = target_map.frame.inverse_frame()
    target_matrix = tuple(tuple(length * value for value in row) for row in inverse.matrix)
    negative_source = tuple(tuple(-value for value in row) for row in source_matrix)
    twists = tuple(_LocalTwist(
        CompiledRationalAffine.from_frame(RationalAffine(
            negative_source, tuple((value - origin) / length
                                   for value, origin in zip(twist.center, source_origin)))),
        twist.radius_squared / (length * length), sign * twist.strength,
    ) for sequence, sign in ((source_map.twists, 1), (reversed(target_map.twists), -1))
        for twist in sequence)
    return CompiledLocalQuantizedPair(
        fractional_bits, length, cancelled,
        CompiledRationalAffine.from_frame(RationalAffine(source_matrix)),
        CompiledRationalAffine.from_frame(RationalAffine(target_matrix)),
        CompiledRationalAffine.from_frame(inverse.after(source_map.frame)), None, twists,
    )
