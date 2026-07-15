from __future__ import annotations

from functools import lru_cache

from .coverage_contract import (
    ACTIVE_COORDINATE_CONTRACT_ID,
    AmbiguousPhysicalCoverage,
    APPROXIMATE_COVERAGE_CONTRACT_ID,
    APPROXIMATE_COVERAGE_METHOD_ID,
    MAX_ACTIVE_HEX_RADIUS,
    MAX_PHYSICAL_LAYER,
    MIN_PHYSICAL_LAYER,
    PhysicalCoverageExpansion,
    PhysicalCoverageMember,
    RELATION_THRESHOLD_Q16,
    SAMPLE_COUNT,
    SAMPLE_SUBDIVISION,
    UnsupportedPhysicalCoverage,
)
from .fixed_point import Q16_ONE, normalize_q16_weights
from .geometry import GeometryAddress
from .profiles import DEFAULT_PROFILE_ID


_Q40_ONE = 1 << 40

# Each tuple is axial matrix q/q,r and local-world matrix q/x,y,r/x,y in Q24.40.
# Values were compiled from beta=2^(1/4) and +/-22.5 degrees at 96-digit precision.
_TRANSFORMS = {
    "coverage_up": (
        649918386859, -408555777664, 408555777664, 1058474164523,
        375230555604, -489009980729, 235879788213, 569464183794,
    ),
    "coverage_down": (
        1496908518890, 577785121758, -577785121758, 919123397132,
        864240536333, -113779425125, -333584395581, 805343972007,
    ),
}

_HEX_VERTICES_Q40 = (
    (952205001410, 549755813888),
    (0, 1099511627776),
    (-952205001410, 549755813888),
    (-952205001410, -549755813888),
    (0, -1099511627776),
    (952205001410, -549755813888),
)


def expand_approximate_coverage(source: GeometryAddress, direction: str) -> PhysicalCoverageExpansion:
    _validate(source, direction)
    return _expand_cached(source, direction)


def clear_approximate_coverage_cache() -> None:
    _expand_cached.cache_clear()


@lru_cache(maxsize=8192)
def _expand_cached(source: GeometryAddress, direction: str) -> PhysicalCoverageExpansion:
    target_layer = source.layer - 1 if direction == "coverage_up" else source.layer + 1
    matrix = _TRANSFORMS[direction]
    hits: dict[tuple[int, int], int] = {}
    for offset_x, offset_y in _sample_offsets_q40():
        q_fixed = (
            matrix[0] * source.q
            + matrix[1] * source.r
            + _round_ratio(matrix[4] * offset_x + matrix[5] * offset_y, _Q40_ONE)
        )
        r_fixed = (
            matrix[2] * source.q
            + matrix[3] * source.r
            + _round_ratio(matrix[6] * offset_x + matrix[7] * offset_y, _Q40_ONE)
        )
        target = _nearest_axial_q40(q_fixed, r_fixed)
        hits[target] = hits.get(target, 0) + 1

    retained = tuple(
        (target, count)
        for target, count in sorted(hits.items())
        if count * Q16_ONE >= RELATION_THRESHOLD_Q16 * SAMPLE_COUNT
    )
    if not retained:
        raise AmbiguousPhysicalCoverage("bounded quadrature produced no relation above threshold")
    if len(retained) > 8:
        raise AmbiguousPhysicalCoverage("bounded quadrature exceeded fanout 8")
    if any(_hex_radius(q, r) > MAX_ACTIVE_HEX_RADIUS for (q, r), _count in retained):
        raise UnsupportedPhysicalCoverage("physical coverage target is outside active hex radius")

    retained_mass = sum(count for _target, count in retained)
    pruned_mass = SAMPLE_COUNT - retained_mass
    weights = normalize_q16_weights([count for _target, count in retained])
    members = []
    max_rounding_residual = 0
    for ((q, r), count), weight in zip(retained, weights):
        numerator_error = abs(weight * retained_mass - count * Q16_ONE)
        rounding_residual = (numerator_error + retained_mass - 1) // retained_mass
        max_rounding_residual = max(max_rounding_residual, rounding_residual)
        members.append(PhysicalCoverageMember(
            GeometryAddress(source.profile_id, source.chart_id, target_layer, q, r, source.phase),
            weight,
            count,
            "bounded_equal_area_quadrature",
            rounding_residual,
        ))
    ordered = tuple(sorted(members, key=lambda member: member.target.stable_key()))
    return PhysicalCoverageExpansion(
        source=source,
        direction=direction,
        members=ordered,
        method_id=APPROXIMATE_COVERAGE_METHOD_ID,
        sample_count=SAMPLE_COUNT,
        threshold_residual_q16=_round_ratio(pruned_mass * Q16_ONE, SAMPLE_COUNT),
        q16_rounding_residual=max_rounding_residual,
        fanout=len(ordered),
        relation_threshold_q16=RELATION_THRESHOLD_Q16,
        q16_sum=sum(member.weight_q16 for member in ordered),
        coordinate_contract_id=ACTIVE_COORDINATE_CONTRACT_ID,
        approximation_contract_id=APPROXIMATE_COVERAGE_CONTRACT_ID,
    )


@lru_cache(maxsize=1)
def _sample_offsets_q40() -> tuple[tuple[int, int], ...]:
    denominator = 3 * SAMPLE_SUBDIVISION
    output = []
    for sector, first in enumerate(_HEX_VERTICES_Q40):
        second = _HEX_VERTICES_Q40[(sector + 1) % 6]
        for i in range(SAMPLE_SUBDIVISION):
            for j in range(SAMPLE_SUBDIVISION - i):
                output.append(_centroid(first, second, 3 * i + 1, 3 * j + 1, denominator))
        for i in range(SAMPLE_SUBDIVISION - 1):
            for j in range(SAMPLE_SUBDIVISION - 1 - i):
                output.append(_centroid(first, second, 3 * i + 2, 3 * j + 2, denominator))
    if len(output) != SAMPLE_COUNT:
        raise RuntimeError("canonical quadrature sample count mismatch")
    return tuple(output)


def _centroid(
    first: tuple[int, int],
    second: tuple[int, int],
    first_weight: int,
    second_weight: int,
    denominator: int,
) -> tuple[int, int]:
    return (
        _round_ratio(first_weight * first[0] + second_weight * second[0], denominator),
        _round_ratio(first_weight * first[1] + second_weight * second[1], denominator),
    )


def _nearest_axial_q40(q_fixed: int, r_fixed: int) -> tuple[int, int]:
    x_fixed, z_fixed, y_fixed = q_fixed, r_fixed, -q_fixed - r_fixed
    x = _round_ratio(x_fixed, _Q40_ONE)
    z = _round_ratio(z_fixed, _Q40_ONE)
    y = _round_ratio(y_fixed, _Q40_ONE)
    dx = abs(x * _Q40_ONE - x_fixed)
    dz = abs(z * _Q40_ONE - z_fixed)
    dy = abs(y * _Q40_ONE - y_fixed)
    if dx >= dz and dx >= dy:
        x = -y - z
    elif dz >= dy:
        z = -x - y
    return x, z


def _round_ratio(numerator: int, denominator: int) -> int:
    sign = -1 if numerator < 0 else 1
    quotient, remainder = divmod(abs(numerator), denominator)
    doubled = remainder * 2
    if doubled > denominator or (doubled == denominator and quotient % 2):
        quotient += 1
    return sign * quotient


def _hex_radius(q: int, r: int) -> int:
    return max(abs(q), abs(r), abs(q + r))


def _validate(source: object, direction: object) -> None:
    if type(source) is not GeometryAddress:
        raise TypeError("source must be GeometryAddress")
    if source.profile_id != DEFAULT_PROFILE_ID:
        raise UnsupportedPhysicalCoverage("physical coverage requires default_dream_v1")
    if source.chart_id != "default":
        raise UnsupportedPhysicalCoverage("physical coverage supports chart_id=default only")
    if source.phase is not None:
        raise UnsupportedPhysicalCoverage("physical coverage supports phase=null only")
    if direction not in _TRANSFORMS:
        raise UnsupportedPhysicalCoverage("physical coverage requires an adjacent-layer direction")
    target_layer = source.layer - 1 if direction == "coverage_up" else source.layer + 1
    if not MIN_PHYSICAL_LAYER <= source.layer <= MAX_PHYSICAL_LAYER or not MIN_PHYSICAL_LAYER <= target_layer <= MAX_PHYSICAL_LAYER:
        raise UnsupportedPhysicalCoverage("physical coverage layer is outside [-64,64]")
    if _hex_radius(source.q, source.r) > MAX_ACTIVE_HEX_RADIUS:
        raise UnsupportedPhysicalCoverage("physical coverage source is outside active hex radius")
