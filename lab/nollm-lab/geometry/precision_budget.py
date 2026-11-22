"""Final-coordinate precision diagnostics for the rational axial contract.

A cell's Voronoi hexagon is |2u+v| <= 1, |u+2v| <= 1, |u-v| <= 1,
where (u,v) is displacement from its integer center. Certified per-axis
coordinate errors therefore give exact, rational face tests. An inconclusive
test returns None; it does not change the coordinate or its geometry contract.

These bounds concern the FINAL target-local axial coordinates. They are not
error estimates for quantized map coefficients, inverse maps or a rounded
nonlinear execution chain. Computing an exact point and then quantizing it
also does not remove the cost of the preceding exact map evaluation.
"""
from __future__ import annotations

from .rational_affine_kernel import nearest_axial_ratio
from .rational_geometry import Q


def _round_ratio(numerator: int, denominator: int) -> int:
    sign = -1 if numerator < 0 else 1
    whole, remainder = divmod(abs(numerator), denominator)
    twice = 2 * remainder
    if twice > denominator or (twice == denominator and whole % 2):
        whole += 1
    return sign * whole


def quantize_axial_ratio(q_num: int, r_num: int, denominator: int,
                         bits: int) -> tuple[int, int, int]:
    """Round each exact coordinate half-even to ``bits`` binary fractional bits.

    Return integer numerators and denominator 2**bits. Integer-range storage is
    independent of this fractional-bit count. Each coordinate error is at most
    2**(-bits-1), without an intermediate float conversion.
    """
    if denominator <= 0:
        raise ValueError("coordinate denominator must be positive")
    if bits < 0:
        raise ValueError("fractional bits must be nonnegative")
    scale = 1 << bits
    return (_round_ratio(q_num * scale, denominator),
            _round_ratio(r_num * scale, denominator), scale)


def _cell_and_margins(q_num, r_num, denominator):
    cell = nearest_axial_ratio(q_num, r_num, denominator)
    u, v = q_num - cell[0] * denominator, r_num - cell[1] * denominator
    margins = (denominator - abs(2 * u + v),
               denominator - abs(u + 2 * v),
               denominator - abs(u - v))
    return cell, margins


def certify_axial_ratio(q_num: int, r_num: int, denominator: int,
                        error_q=0, error_r=None) -> tuple[int, int] | None:
    """Certify the same target for every point in the supplied error rectangle.

    The center is (q_num,r_num)/denominator; error bounds must be trustworthy,
    nonnegative exact int/Fraction/text values. error_r defaults to error_q.
    Strict interior containment is sufficient. None means not certified by
    this test, not necessarily a changed label. Zero error uses the exact
    half-even/cube tie contract, including a point exactly on a hexagon face.
    """
    error_q = Q(error_q)
    error_r = error_q if error_r is None else Q(error_r)
    if error_q < 0 or error_r < 0:
        raise ValueError("coordinate error bounds must be nonnegative")
    cell, margins = _cell_and_margins(q_num, r_num, denominator)
    if error_q == 0 and error_r == 0:
        return cell
    errors = (2 * error_q + error_r, error_q + 2 * error_r, error_q + error_r)
    if all(margin * error.denominator > denominator * error.numerator
           for margin, error in zip(margins, errors)):
        return cell
    return None


def minimum_safe_fraction_bits(q_num: int, r_num: int,
                               denominator: int) -> int | None:
    """Smallest nonnegative p passing the strict final-coordinate certificate.

    Every error with |dq|,|dr| <= 2**(-p-1) then preserves the exact point's
    target. This is a conservative precision certificate, not necessarily the
    least p at which one particular deterministic rounding happens to agree.
    Boundary points return None: a positive two-dimensional error rectangle
    cannot be strictly contained in one target cell, even if a given rounding
    happens to retain the tie. Larger p keep a successful certificate valid.
    """
    _, (m1, m2, m3) = _cell_and_margins(q_num, r_num, denominator)
    if min(m1, m2, m3) <= 0:
        return None
    # For integer S=2**p, S > n/d iff S > floor(n/d). The least such p is
    # floor(n/d).bit_length(), including the n<d case where p=0.
    return max((3 * denominator // (2 * m1)).bit_length(),
               (3 * denominator // (2 * m2)).bit_length(),
               (denominator // m3).bit_length())
