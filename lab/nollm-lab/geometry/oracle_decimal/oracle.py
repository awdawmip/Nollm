from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN, localcontext


PRECISION = 96
PI = Decimal("3.141592653589793238462643383279502884197169399375105820974944592307816406286208998628034825")
POSITIVE_THRESHOLD = Decimal("1e-70")
MIN_COORDINATE = -(1 << 63)
MAX_COORDINATE = (1 << 63) - 1
MIN_LAYER = -64
MAX_LAYER = 64


@dataclass(frozen=True, order=True)
class CoverageMember:
    q: int
    r: int
    intersection_area: Decimal
    source_share: Decimal
    target_share: Decimal


def _beta() -> Decimal:
    with localcontext() as context:
        context.prec = PRECISION
        return Decimal(2).sqrt().sqrt()


def _relative_side(source_layer: int, target_layer: int) -> Decimal:
    with localcontext() as context:
        context.prec = PRECISION
        return +(_beta() ** Decimal(source_layer - target_layer))


def _relative_angle(source_layer: int, target_layer: int) -> Decimal:
    return PI * Decimal(target_layer - source_layer) / Decimal(8)


def _sin_cos(angle: Decimal) -> tuple[Decimal, Decimal]:
    with localcontext() as context:
        context.prec = PRECISION
        angle %= PI * 2
        if angle > PI:
            angle -= PI * 2
        sine = sine_term = angle
        cosine = cosine_term = Decimal(1)
        square = angle * angle
        for index in range(1, 120):
            sine_term *= -square / Decimal((2 * index) * (2 * index + 1))
            cosine_term *= -square / Decimal((2 * index - 1) * (2 * index))
            sine += sine_term
            cosine += cosine_term
            if abs(sine_term) < Decimal("1e-90") and abs(cosine_term) < Decimal("1e-90"):
                break
        return +sine, +cosine


def _axial_world(q: Decimal, r: Decimal) -> tuple[Decimal, Decimal]:
    with localcontext() as context:
        context.prec = PRECISION
        return +(Decimal(3).sqrt() * (q + r / 2)), +(Decimal(3) * r / 2)


def _rotate(x: Decimal, y: Decimal, angle: Decimal) -> tuple[Decimal, Decimal]:
    sine, cosine = _sin_cos(angle)
    return +(cosine * x - sine * y), +(sine * x + cosine * y)


def fractional_target_axial(source_layer: int, q: int, r: int, target_layer: int) -> tuple[Decimal, Decimal]:
    _validate(source_layer, q, r, target_layer, 1)
    with localcontext() as context:
        context.prec = PRECISION
        source_x, source_y = _axial_world(Decimal(q), Decimal(r))
        target_x, target_y = _rotate(source_x, source_y, -_relative_angle(source_layer, target_layer))
        ratio = _relative_side(source_layer, target_layer)
        target_x /= ratio
        target_y /= ratio
        target_r = Decimal(2) * target_y / 3
        target_q = target_x / Decimal(3).sqrt() - target_r / 2
        return +target_q, +target_r


def _local_hex_vertices(
    center_x: Decimal,
    center_y: Decimal,
    side: Decimal,
    angle: Decimal,
) -> tuple[tuple[Decimal, Decimal], ...]:
    with localcontext() as context:
        context.prec = PRECISION
        output = []
        for index in range(6):
            sine, cosine = _sin_cos(angle + PI / 6 + PI * Decimal(index) / 3)
            output.append((+(center_x + side * cosine), +(center_y + side * sine)))
        return tuple(output)


def hex_vertices(layer: int, q: int, r: int) -> tuple[tuple[Decimal, Decimal], ...]:
    if type(layer) is not int or type(q) is not int or type(r) is not int:
        raise TypeError("hex address fields must be integers")
    if not MIN_LAYER <= layer <= MAX_LAYER or not MIN_COORDINATE <= q <= MAX_COORDINATE or not MIN_COORDINATE <= r <= MAX_COORDINATE:
        raise ValueError("hex address is outside the supported coordinate domain")
    center_x, center_y = _axial_world(Decimal(q), Decimal(r))
    return _local_hex_vertices(center_x, center_y, Decimal(1), Decimal(0))


def _nearest(qf: Decimal, rf: Decimal) -> tuple[int, int]:
    xf, zf, yf = qf, rf, -qf - rf
    x = int(xf.to_integral_value(rounding=ROUND_HALF_EVEN))
    z = int(zf.to_integral_value(rounding=ROUND_HALF_EVEN))
    y = int(yf.to_integral_value(rounding=ROUND_HALF_EVEN))
    dx, dz, dy = abs(Decimal(x) - xf), abs(Decimal(z) - zf), abs(Decimal(y) - yf)
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


def _area(vertices: tuple[tuple[Decimal, Decimal], ...] | list[tuple[Decimal, Decimal]]) -> Decimal:
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
    if abs(denominator) < Decimal("1e-88"):
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
            current_inside = _cross(edge_start, edge_end, current) >= Decimal("-1e-84")
            previous_inside = _cross(edge_start, edge_end, previous) >= Decimal("-1e-84")
            if current_inside:
                if not previous_inside:
                    output.append(_line_intersection(previous, current, edge_start, edge_end))
                output.append(current)
            elif previous_inside:
                output.append(_line_intersection(previous, current, edge_start, edge_end))
            previous = current
    return _area(output)


def coverage(source_layer: int, q: int, r: int, target_layer: int, candidate_radius: int = 4) -> tuple[CoverageMember, ...]:
    _validate(source_layer, q, r, target_layer, candidate_radius)
    with localcontext() as context:
        context.prec = PRECISION
        qf, rf = fractional_target_axial(source_layer, q, r, target_layer)
        nearest_q, nearest_r = _nearest(qf, rf)
        source = _local_hex_vertices(Decimal(0), Decimal(0), Decimal(1), Decimal(0))
        source_area = _area(source)
        target_side = _relative_side(source_layer, target_layer)
        target_angle = _relative_angle(source_layer, target_layer)
        target_area = source_area * target_side * target_side
        output = []
        for target_q, target_r in _disk(nearest_q, nearest_r, candidate_radius):
            residual_q = Decimal(target_q) - qf
            residual_r = Decimal(target_r) - rf
            local_x, local_y = _axial_world(residual_q, residual_r)
            center_x, center_y = _rotate(target_side * local_x, target_side * local_y, target_angle)
            target = _local_hex_vertices(center_x, center_y, target_side, target_angle)
            intersection = _intersection_area(source, target)
            if intersection > POSITIVE_THRESHOLD:
                output.append(CoverageMember(target_q, target_r, intersection, intersection / source_area, intersection / target_area))
        return tuple(sorted(output))


def _validate(source_layer: object, q: object, r: object, target_layer: object, candidate_radius: object) -> None:
    if any(type(value) is not int for value in (source_layer, q, r, target_layer, candidate_radius)):
        raise TypeError("coverage address fields and candidate radius must be integers")
    if not MIN_LAYER <= source_layer <= MAX_LAYER or not MIN_LAYER <= target_layer <= MAX_LAYER:
        raise ValueError("coverage layer is outside the supported coordinate domain")
    if not MIN_COORDINATE <= q <= MAX_COORDINATE or not MIN_COORDINATE <= r <= MAX_COORDINATE:
        raise ValueError("coverage q/r is outside the supported signed-64 coordinate domain")
    if abs(target_layer - source_layer) != 1 or candidate_radius < 1:
        raise ValueError("coverage requires adjacent layers and a positive candidate radius")
