"""One-pass fixed-point execution of the explicit rational Lab geometry.

This is a distinct numerical contract: sample targets may differ from the exact
rational maps. The caller chooses one fractional precision for the whole pass;
there is no interval certification, precision escalation or exact repair.
Rational parameters remain the inputs. Common outer twists and a common world
anchor cancel before compilation. Pure affine pairs retain the inexpensive
existing exact integer kernel; fixed-point execution applies to nonlinear work.

Every rounded operation uses signed half-even. Integer products and fused row
numerators are wide intermediates; retained coordinates, norms, cutoffs and twist
parameters use S=2**fractional_bits. Twist centers are rounded once at compilation.
The positive radius reciprocal and strength remain exact scalar ratios, avoiding
a zero denominator when a small positive radius² is below one fixed-point step.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from .rational_affine_kernel import (
    CompiledRationalAffine, _round_ratio, compile_affine_pair, nearest_axial_ratio,
)
from .rational_geometry import RationalLayerMap, RationalRadialTwist, relative_layer_maps


@dataclass(frozen=True)
class _QuantizedTwist:
    center_q: int
    center_r: int
    radius_numerator: int
    radius_denominator: int
    strength_numerator: int
    strength_denominator: int

    @classmethod
    def from_twist(cls, twist: RationalRadialTwist, sign: int, scale: int):
        q, r = twist.center
        radius, strength = twist.radius_squared, sign * twist.strength
        return cls(_round_ratio(q.numerator * scale, q.denominator),
                   _round_ratio(r.numerator * scale, r.denominator),
                   radius.numerator, radius.denominator,
                   strength.numerator, strength.denominator)

    def apply(self, q: int, r: int, scale: int) -> tuple[int, int]:
        """Apply the declared fused fixed-point recurrence once."""
        u, v = q - self.center_q, r - self.center_r
        norm = _round_ratio(u*u + u*v + v*v, scale)
        normalized = _round_ratio(norm * self.radius_denominator, self.radius_numerator)
        cutoff = max(0, scale - normalized)
        parameter = _round_ratio(_round_ratio(cutoff*cutoff, scale)
                                 * self.strength_numerator, self.strength_denominator)
        if parameter == 0:
            return q, r
        t2 = _round_ratio(parameter * parameter, scale)
        denominator, middle = scale + 3*t2, scale - 3*t2
        mapped_q = _round_ratio((middle - 2*parameter)*u - 4*parameter*v, denominator)
        mapped_r = _round_ratio(4*parameter*u + (middle + 2*parameter)*v, denominator)
        return mapped_q + self.center_q, mapped_r + self.center_r


@dataclass(frozen=True)
class CompiledQuantizedPair:
    """Reusable coefficients for a single chosen nonlinear fractional precision."""

    fractional_bits: int
    cancelled_common_twists: int
    _source_kernel: CompiledRationalAffine | None
    _target_kernel: CompiledRationalAffine | None
    _affine_kernel: CompiledRationalAffine | None
    _twists: tuple[_QuantizedTwist, ...]

    @property
    def execution_kind(self) -> str:
        return "integer_affine" if self._affine_kernel is not None else "fixed_point_nonlinear"

    def map_ratio(self, q_num: int, r_num: int, denominator: int = 1) -> tuple[int, int, int]:
        """Map a common-denominator input under the selected execution contract.

        Nonlinear results have denominator 2**fractional_bits. Pure affine
        results keep the exact compiled denominator rather than adding work
        and rounding error to an already inexpensive integer calculation.
        """
        if self._affine_kernel is not None:
            return self._affine_kernel.map_ratio(q_num, r_num, denominator)
        scale = 1 << self.fractional_bits
        q, r, divisor = self._source_kernel.map_ratio(q_num, r_num, denominator)
        q, r = _round_ratio(q * scale, divisor), _round_ratio(r * scale, divisor)
        for twist in self._twists:
            q, r = twist.apply(q, r, scale)
        q, r, divisor = self._target_kernel.map_ratio(q, r, scale)
        return _round_ratio(q * scale, divisor), _round_ratio(r * scale, divisor), scale

    def targets(self, q: int, r: int, offset_numerators: tuple[tuple[int, int], ...],
                offset_denominator: int) -> tuple[tuple[int, int], ...]:
        """Return one target per sample after one fixed-precision execution."""
        if offset_denominator <= 0:
            raise ValueError("sample denominator must be positive")
        if self._affine_kernel is not None:
            return self._affine_kernel.targets(q, r, offset_numerators, offset_denominator)
        base_q, base_r = q * offset_denominator, r * offset_denominator
        return tuple(nearest_axial_ratio(*self.map_ratio(base_q + dq, base_r + dr,
                                                         offset_denominator))
                     for dq, dr in offset_numerators)


def compile_quantized_pair(source_map: RationalLayerMap, target_map: RationalLayerMap,
                           *, fractional_bits: int = 12) -> CompiledQuantizedPair:
    """Compile a one-pass experiment; fractional_bits controls nonlinear rounding.

    Identical ordered outer suffixes cancel exactly before quantization. A
    common world translation is removed exactly, including twist centers.
    Different transforms retain their order. The resulting approximate target
    labels are accepted directly as the selected sampled geometry.
    """
    if fractional_bits < 0:
        raise ValueError("fractional bits must be nonnegative")
    affine = compile_affine_pair(source_map, target_map)
    if affine is not None:
        return CompiledQuantizedPair(fractional_bits, len(source_map.twists),
                                     None, None, affine, ())
    source_twists, target_twists = source_map.twists, target_map.twists
    cancelled = 0
    while (cancelled < min(len(source_twists), len(target_twists))
           and source_twists[-1-cancelled] == target_twists[-1-cancelled]):
        cancelled += 1
    if cancelled:
        source_map = replace(source_map, twists=source_twists[:-cancelled])
        target_map = replace(target_map, twists=target_twists[:-cancelled])
    source_map, target_map = relative_layer_maps(source_map, target_map)
    scale = 1 << fractional_bits
    twists = tuple(_QuantizedTwist.from_twist(twist, sign, scale)
                   for sequence, sign in ((source_map.twists, 1),
                                          (reversed(target_map.twists), -1))
                   for twist in sequence if twist.strength != 0)
    return CompiledQuantizedPair(
        fractional_bits, cancelled, CompiledRationalAffine.from_frame(source_map.frame),
        CompiledRationalAffine.from_frame(target_map.frame.inverse_frame()), None, twists,
    )
