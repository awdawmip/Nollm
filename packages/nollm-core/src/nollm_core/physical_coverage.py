from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_FLOOR, ROUND_HALF_EVEN, localcontext
from functools import lru_cache

from .fixed_point import Q16_ONE
from .geometry import GeometryAddress
from .profiles import DEFAULT_PROFILE_ID


_PRECISION = 80
_PI = Decimal("3.14159265358979323846264338327950288419716939937510582097494459230781640628620899")
_POSITIVE_AREA = Decimal("1e-48")
_PARALLEL_EPSILON = Decimal("1e-72")
_INSIDE_EPSILON = Decimal("1e-68")
# The adjacent-layer circumradius sum is below four target-cell center spacings.
_ADJACENT_CANDIDATE_RADIUS = 4


@dataclass(frozen=True, order=True)
class PhysicalCoverageMember:
    target: GeometryAddress
    weight_q16: int
    intersection_area: str
    source_share: str
    target_share: str
    quantization_residual_q16: int


@dataclass(frozen=True)
class PhysicalCoverageExpansion:
    source: GeometryAddress
    direction: str
    members: tuple[PhysicalCoverageMember, ...]
    sum_weight_q16: int
    normalization_residual_q16: int
    max_quantization_residual_q16: int
    candidate_radius: int = _ADJACENT_CANDIDATE_RADIUS

    def targets(self) -> tuple[tuple[GeometryAddress, int], ...]:
        return tuple((member.target, member.weight_q16) for member in self.members)


def expand_physical_coverage(source: GeometryAddress, direction: str) -> PhysicalCoverageExpansion:
    if type(source) is not GeometryAddress:
        raise TypeError("source must be GeometryAddress")
    if source.profile_id != DEFAULT_PROFILE_ID:
        raise ValueError("physical coverage requires default_dream_v1")
    if direction not in ("coverage_up", "coverage_down"):
        raise ValueError("physical coverage requires an adjacent-layer direction")
    return _expand_cached(source, direction)


def clear_physical_coverage_cache() -> None:
    _expand_cached.cache_clear()
    _vertices.cache_clear()
    _center.cache_clear()
    _layer_constants.cache_clear()


@lru_cache(maxsize=8192)
def _expand_cached(source: GeometryAddress, direction: str) -> PhysicalCoverageExpansion:
    target_layer = source.layer - 1 if direction == "coverage_up" else source.layer + 1
    source_polygon = _vertices(source.layer, source.q, source.r)
    source_area = _polygon_area(source_polygon)
    fractional_q, fractional_r = _fractional_target(source.layer, source.q, source.r, target_layer)
    center_q, center_r = _nearest_axial(fractional_q, fractional_r)
    raw = []
    for target_q, target_r in _disk(center_q, center_r, _ADJACENT_CANDIDATE_RADIUS):
        target_polygon = _vertices(target_layer, target_q, target_r)
        intersection = _intersection_area(source_polygon, target_polygon)
        if intersection > _POSITIVE_AREA:
            raw.append((target_q, target_r, intersection, intersection / source_area, intersection / _polygon_area(target_polygon)))
    if not raw:
        raise ValueError("physical coverage produced no positive overlap")
    weights = _quantize(tuple(item[3] for item in raw))
    members = []
    max_residual = 0
    for item, weight in zip(raw, weights):
        ideal = item[3] * Q16_ONE
        residual = int(abs(Decimal(weight) - ideal).to_integral_value(rounding="ROUND_CEILING"))
        max_residual = max(max_residual, residual)
        members.append(
            PhysicalCoverageMember(
                GeometryAddress(source.profile_id, source.chart_id, target_layer, item[0], item[1], source.phase),
                weight,
                _decimal_text(item[2]),
                _decimal_text(item[3]),
                _decimal_text(item[4]),
                residual,
            )
        )
    ordered = tuple(sorted(members, key=lambda member: member.target.stable_key()))
    total = sum(member.weight_q16 for member in ordered)
    return PhysicalCoverageExpansion(source, direction, ordered, total, Q16_ONE - total, max_residual)


def _quantize(shares: tuple[Decimal, ...]) -> tuple[int, ...]:
    scaled = tuple(share * Q16_ONE for share in shares)
    weights = [max(1, int(value.to_integral_value(rounding=ROUND_FLOOR))) for value in scaled]
    delta = Q16_ONE - sum(weights)
    if delta > 0:
        order = sorted(range(len(weights)), key=lambda index: (-(scaled[index] - Decimal(weights[index])), index))
        for index in order[:delta]:
            weights[index] += 1
    elif delta < 0:
        order = sorted(range(len(weights)), key=lambda index: (-weights[index], index))
        for index in order:
            take = min(weights[index] - 1, -delta)
            weights[index] -= take
            delta += take
            if delta == 0:
                break
    if sum(weights) != Q16_ONE or any(weight <= 0 for weight in weights):
        raise ValueError("physical coverage Q16 normalization failed")
    return tuple(weights)


@lru_cache(maxsize=128)
def _layer_constants(layer: int) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    with localcontext() as context:
        context.prec = _PRECISION
        beta = Decimal(2).sqrt().sqrt()
        side = beta ** Decimal(-layer)
        sine, cosine = _sin_cos(_PI * Decimal(layer) / Decimal(8))
        return +side, +Decimal(3).sqrt(), +sine, +cosine


@lru_cache(maxsize=32768)
def _center(layer: int, q: int, r: int) -> tuple[Decimal, Decimal]:
    with localcontext() as context:
        context.prec = _PRECISION
        side, root3, sine, cosine = _layer_constants(layer)
        local_x = root3 * side * (Decimal(q) + Decimal(r) / 2)
        local_y = Decimal(3) * side * Decimal(r) / 2
        return +(cosine * local_x - sine * local_y), +(sine * local_x + cosine * local_y)


@lru_cache(maxsize=32768)
def _vertices(layer: int, q: int, r: int) -> tuple[tuple[Decimal, Decimal], ...]:
    with localcontext() as context:
        context.prec = _PRECISION
        center_x, center_y = _center(layer, q, r)
        side, _, _, _ = _layer_constants(layer)
        output = []
        for index in range(6):
            sine, cosine = _sin_cos(_PI * Decimal(layer) / Decimal(8) + _PI / 6 + _PI * Decimal(index) / 3)
            output.append((+(center_x + side * cosine), +(center_y + side * sine)))
        return tuple(output)


def _fractional_target(source_layer: int, q: int, r: int, target_layer: int) -> tuple[Decimal, Decimal]:
    with localcontext() as context:
        context.prec = _PRECISION
        world_x, world_y = _center(source_layer, q, r)
        target_side, root3, target_sine, target_cosine = _layer_constants(target_layer)
        local_x = target_cosine * world_x + target_sine * world_y
        local_y = -target_sine * world_x + target_cosine * world_y
        target_r = Decimal(2) * local_y / (Decimal(3) * target_side)
        target_q = local_x / (root3 * target_side) - target_r / 2
        return +target_q, +target_r


def _sin_cos(angle: Decimal) -> tuple[Decimal, Decimal]:
    with localcontext() as context:
        context.prec = _PRECISION
        angle %= _PI * 2
        if angle > _PI:
            angle -= _PI * 2
        sine = sine_term = angle
        cosine = cosine_term = Decimal(1)
        square = angle * angle
        for index in range(1, 96):
            sine_term *= -square / Decimal((2 * index) * (2 * index + 1))
            cosine_term *= -square / Decimal((2 * index - 1) * (2 * index))
            sine += sine_term
            cosine += cosine_term
            if abs(sine_term) < Decimal("1e-76") and abs(cosine_term) < Decimal("1e-76"):
                break
        return +sine, +cosine


def _nearest_axial(q: Decimal, r: Decimal) -> tuple[int, int]:
    x_fraction, z_fraction, y_fraction = q, r, -q - r
    x = int(x_fraction.to_integral_value(rounding=ROUND_HALF_EVEN))
    z = int(z_fraction.to_integral_value(rounding=ROUND_HALF_EVEN))
    y = int(y_fraction.to_integral_value(rounding=ROUND_HALF_EVEN))
    dx, dz, dy = abs(Decimal(x) - x_fraction), abs(Decimal(z) - z_fraction), abs(Decimal(y) - y_fraction)
    if dx >= dz and dx >= dy:
        x = -y - z
    elif dz >= dy:
        z = -x - y
    return x, z


def _disk(center_q: int, center_r: int, radius: int) -> tuple[tuple[int, int], ...]:
    return tuple(
        (center_q + dq, center_r + dr)
        for dq in range(-radius, radius + 1)
        for dr in range(max(-radius, -dq - radius), min(radius, -dq + radius) + 1)
    )


def _polygon_area(vertices) -> Decimal:
    if len(vertices) < 3:
        return Decimal(0)
    total = Decimal(0)
    for index, point in enumerate(vertices):
        following = vertices[(index + 1) % len(vertices)]
        total += point[0] * following[1] - point[1] * following[0]
    return abs(total) / 2


def _cross(a, b, c) -> Decimal:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _line_intersection(a, b, c, d):
    ab = b[0] - a[0], b[1] - a[1]
    cd = d[0] - c[0], d[1] - c[1]
    denominator = ab[0] * cd[1] - ab[1] * cd[0]
    if abs(denominator) < _PARALLEL_EPSILON:
        return b
    factor = ((c[0] - a[0]) * cd[1] - (c[1] - a[1]) * cd[0]) / denominator
    return a[0] + factor * ab[0], a[1] + factor * ab[1]


def _intersection_area(subject, clipper) -> Decimal:
    output = list(subject)
    for index, edge_start in enumerate(clipper):
        edge_end = clipper[(index + 1) % len(clipper)]
        points, output = output, []
        if not points:
            break
        previous = points[-1]
        for current in points:
            current_inside = _cross(edge_start, edge_end, current) >= -_INSIDE_EPSILON
            previous_inside = _cross(edge_start, edge_end, previous) >= -_INSIDE_EPSILON
            if current_inside:
                if not previous_inside:
                    output.append(_line_intersection(previous, current, edge_start, edge_end))
                output.append(current)
            elif previous_inside:
                output.append(_line_intersection(previous, current, edge_start, edge_end))
            previous = current
    return _polygon_area(output)


def _decimal_text(value: Decimal) -> str:
    return format(+value, "f")
