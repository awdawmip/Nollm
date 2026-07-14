from __future__ import annotations

from decimal import Decimal, getcontext, localcontext


PI = Decimal("3.141592653589793238462643383279502884197169399375105820974944592307816406286")
Q16_ONE = 1 << 16
Q32_ONE = 1 << 32
getcontext().prec = 72


def beta() -> Decimal:
    with localcontext() as context:
        context.prec = 72
        return Decimal(2).sqrt().sqrt()


def sin_cos(angle: Decimal) -> tuple[Decimal, Decimal]:
    with localcontext() as context:
        context.prec = 72
        two_pi = PI * 2
        angle %= two_pi
        if angle > PI:
            angle -= two_pi
        sine = angle
        cosine = Decimal(1)
        sine_term = angle
        cosine_term = Decimal(1)
        square = angle * angle
        for index in range(1, 80):
            sine_term *= -square / Decimal((2 * index) * (2 * index + 1))
            cosine_term *= -square / Decimal((2 * index - 1) * (2 * index))
            sine += sine_term
            cosine += cosine_term
            if abs(sine_term) < Decimal("1e-68") and abs(cosine_term) < Decimal("1e-68"):
                break
        return +sine, +cosine


def layer_angle(layer: int) -> Decimal:
    return PI * Decimal(layer) / Decimal(8)


def layer_side(layer: int) -> Decimal:
    with localcontext() as context:
        context.prec = 72
        return beta() ** Decimal(-layer)


def axial_transform_q32(direction: str) -> tuple[int, int, int, int]:
    if direction == "lateral":
        return (Q32_ONE, 0, 0, Q32_ONE)
    source_layer = 0
    target_layer = -1 if direction == "coverage_up" else 1
    source_side, target_side = layer_side(source_layer), layer_side(target_layer)
    sine, cosine = sin_cos(layer_angle(source_layer) - layer_angle(target_layer))
    root3 = Decimal(3).sqrt()
    # B^-1 R(delta) (source_side / target_side) B for pointy-top axial B.
    scale = source_side / target_side
    a = scale * (cosine + sine / root3)
    b = scale * (Decimal(2) * sine / root3)
    c = scale * (-Decimal(2) * sine / root3)
    d = scale * (cosine - sine / root3)
    return tuple(int((value * Q32_ONE).to_integral_value(rounding="ROUND_HALF_EVEN")) for value in (a, b, c, d))


def hex_center(layer: int, q: int, r: int) -> tuple[Decimal, Decimal]:
    side = layer_side(layer)
    root3 = Decimal(3).sqrt()
    local_x = root3 * side * (Decimal(q) + Decimal(r) / 2)
    local_y = Decimal(3) * side * Decimal(r) / 2
    sine, cosine = sin_cos(layer_angle(layer))
    return cosine * local_x - sine * local_y, sine * local_x + cosine * local_y


def hex_vertices(layer: int, q: int, r: int) -> tuple[tuple[Decimal, Decimal], ...]:
    center_x, center_y = hex_center(layer, q, r)
    side = layer_side(layer)
    vertices = []
    for index in range(6):
        angle = layer_angle(layer) + PI / 6 + PI * Decimal(index) / 3
        sine, cosine = sin_cos(angle)
        vertices.append((center_x + side * cosine, center_y + side * sine))
    return tuple(vertices)


def polygon_area(polygon: tuple[tuple[Decimal, Decimal], ...] | list[tuple[Decimal, Decimal]]) -> Decimal:
    if len(polygon) < 3:
        return Decimal(0)
    total = Decimal(0)
    for index, point in enumerate(polygon):
        following = polygon[(index + 1) % len(polygon)]
        total += point[0] * following[1] - point[1] * following[0]
    return abs(total) / 2


def intersection_area(
    subject: tuple[tuple[Decimal, Decimal], ...],
    clip: tuple[tuple[Decimal, Decimal], ...],
) -> Decimal:
    output = list(subject)
    for index, edge_start in enumerate(clip):
        edge_end = clip[(index + 1) % len(clip)]
        input_points, output = output, []
        if not input_points:
            break
        previous = input_points[-1]
        for current in input_points:
            current_inside = _inside(edge_start, edge_end, current)
            previous_inside = _inside(edge_start, edge_end, previous)
            if current_inside:
                if not previous_inside:
                    output.append(_intersection(previous, current, edge_start, edge_end))
                output.append(current)
            elif previous_inside:
                output.append(_intersection(previous, current, edge_start, edge_end))
            previous = current
    return polygon_area(output)


def canonical_overlap(from_layer_mod: int, direction: str, dq: int, dr: int) -> tuple[Decimal, Decimal, Decimal]:
    target_layer = from_layer_mod + (-1 if direction == "coverage_up" else 1)
    source = hex_vertices(from_layer_mod, 0, 0)
    target = hex_vertices(target_layer, dq, dr)
    area = intersection_area(source, target)
    return area, area / polygon_area(source), area / polygon_area(target)


def decimal_text(value: Decimal) -> str:
    with localcontext() as context:
        context.prec = 80
        return format(value.quantize(Decimal("1e-48")), "f")


def q16(value: Decimal) -> int:
    return max(0, min(Q16_ONE, int((value * Q16_ONE).to_integral_value(rounding="ROUND_HALF_EVEN"))))


def _inside(start: tuple[Decimal, Decimal], end: tuple[Decimal, Decimal], point: tuple[Decimal, Decimal]) -> bool:
    return (end[0] - start[0]) * (point[1] - start[1]) - (end[1] - start[1]) * (point[0] - start[0]) >= Decimal("-1e-60")


def _intersection(p1, p2, q1, q2):
    rx, ry = p2[0] - p1[0], p2[1] - p1[1]
    sx, sy = q2[0] - q1[0], q2[1] - q1[1]
    denominator = rx * sy - ry * sx
    if abs(denominator) < Decimal("1e-64"):
        return p2
    t = ((q1[0] - p1[0]) * sy - (q1[1] - p1[1]) * sx) / denominator
    return p1[0] + t * rx, p1[1] + t * ry
