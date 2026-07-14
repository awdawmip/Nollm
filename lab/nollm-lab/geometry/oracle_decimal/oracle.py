from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_FLOOR, ROUND_HALF_EVEN, localcontext


PRECISION = 80
PI = Decimal("3.14159265358979323846264338327950288419716939937510582097494459230781640628620899")
POSITIVE_THRESHOLD = Decimal("1e-48")


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


def _side(layer: int) -> Decimal:
    with localcontext() as context:
        context.prec = PRECISION
        return _beta() ** Decimal(-layer)


def _angle(layer: int) -> Decimal:
    return PI * Decimal(layer) / Decimal(8)


def _sin_cos(angle: Decimal) -> tuple[Decimal, Decimal]:
    with localcontext() as context:
        context.prec = PRECISION
        angle %= PI * 2
        if angle > PI:
            angle -= PI * 2
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


def _center(layer: int, q: int, r: int) -> tuple[Decimal, Decimal]:
    with localcontext() as context:
        context.prec = PRECISION
        side = _side(layer)
        root3 = Decimal(3).sqrt()
        x = root3 * side * (Decimal(q) + Decimal(r) / 2)
        y = Decimal(3) * side * Decimal(r) / 2
        sine, cosine = _sin_cos(_angle(layer))
        return +(cosine * x - sine * y), +(sine * x + cosine * y)


def hex_vertices(layer: int, q: int, r: int) -> tuple[tuple[Decimal, Decimal], ...]:
    with localcontext() as context:
        context.prec = PRECISION
        center_x, center_y = _center(layer, q, r)
        side = _side(layer)
        output = []
        for index in range(6):
            sine, cosine = _sin_cos(_angle(layer) + PI / 6 + PI * Decimal(index) / 3)
            output.append((+(center_x + side * cosine), +(center_y + side * sine)))
        return tuple(output)


def fractional_target_axial(source_layer: int, q: int, r: int, target_layer: int) -> tuple[Decimal, Decimal]:
    with localcontext() as context:
        context.prec = PRECISION
        world_x, world_y = _center(source_layer, q, r)
        sine, cosine = _sin_cos(-_angle(target_layer))
        local_x = cosine * world_x - sine * world_y
        local_y = sine * world_x + cosine * world_y
        side = _side(target_layer)
        target_r = Decimal(2) * local_y / (Decimal(3) * side)
        target_q = local_x / (Decimal(3).sqrt() * side) - target_r / 2
        return +target_q, +target_r


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
    output = []
    for dq in range(-radius, radius + 1):
        for dr in range(max(-radius, -dq - radius), min(radius, -dq + radius) + 1):
            output.append((center_q + dq, center_r + dr))
    return tuple(sorted(output))


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
    ab = (b[0] - a[0], b[1] - a[1])
    cd = (d[0] - c[0], d[1] - c[1])
    denominator = ab[0] * cd[1] - ab[1] * cd[0]
    if abs(denominator) < Decimal("1e-72"):
        return b
    t = ((c[0] - a[0]) * cd[1] - (c[1] - a[1]) * cd[0]) / denominator
    return a[0] + t * ab[0], a[1] + t * ab[1]


def _intersection_area(subject, clipper) -> Decimal:
    output = list(subject)
    for index, edge_start in enumerate(clipper):
        edge_end = clipper[(index + 1) % len(clipper)]
        points, output = output, []
        if not points:
            break
        previous = points[-1]
        for current in points:
            current_inside = _cross(edge_start, edge_end, current) >= Decimal("-1e-68")
            previous_inside = _cross(edge_start, edge_end, previous) >= Decimal("-1e-68")
            if current_inside:
                if not previous_inside:
                    output.append(_line_intersection(previous, current, edge_start, edge_end))
                output.append(current)
            elif previous_inside:
                output.append(_line_intersection(previous, current, edge_start, edge_end))
            previous = current
    return _area(output)


def coverage(source_layer: int, q: int, r: int, target_layer: int, candidate_radius: int = 4) -> tuple[CoverageMember, ...]:
    if type(source_layer) is not int or type(target_layer) is not int or type(q) is not int or type(r) is not int:
        raise TypeError("coverage address fields must be integers")
    if abs(target_layer - source_layer) != 1 or type(candidate_radius) is not int or candidate_radius < 1:
        raise ValueError("coverage requires adjacent layers and a positive candidate radius")
    source = hex_vertices(source_layer, q, r)
    source_area = _area(source)
    qf, rf = fractional_target_axial(source_layer, q, r, target_layer)
    nearest_q, nearest_r = _nearest(qf, rf)
    output = []
    for target_q, target_r in _disk(nearest_q, nearest_r, candidate_radius):
        target = hex_vertices(target_layer, target_q, target_r)
        intersection = _intersection_area(source, target)
        if intersection > POSITIVE_THRESHOLD:
            output.append(CoverageMember(target_q, target_r, intersection, intersection / source_area, intersection / _area(target)))
    return tuple(sorted(output))
