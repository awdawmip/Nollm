"""Convex polygon overlap for the DG1 V2 geometry kernel.

Allowed: audited Sutherland-Hodgman clipping for convex CCW polygons and
conservative candidate filtering.
Forbidden: bounding-box-only coverage, nearest-center confirmation, Field,
Cortex, Recall, Adapter, V1, OpenClaw, runtime, filesystem, network,
subprocess, or memory behavior.
"""

from .types import DEFAULT_TOLERANCE, GeometryTolerance, HexCell, Vec2


def signed_polygon_area(vertices: tuple[Vec2, ...] | list[Vec2]) -> float:
    if len(vertices) < 3:
        return 0.0
    total = 0.0
    for index, point in enumerate(vertices):
        nxt = vertices[(index + 1) % len(vertices)]
        total += point.x * nxt.y - nxt.x * point.y
    return total / 2.0


def polygon_area(vertices: tuple[Vec2, ...] | list[Vec2]) -> float:
    area = abs(signed_polygon_area(vertices))
    return 0.0 if area <= DEFAULT_TOLERANCE.area_abs_tol else area


def clip_convex_polygon(
    subject: tuple[Vec2, ...] | list[Vec2],
    clipper: tuple[Vec2, ...] | list[Vec2],
    tolerance: GeometryTolerance = DEFAULT_TOLERANCE,
) -> tuple[Vec2, ...]:
    if len(subject) < 3 or len(clipper) < 3:
        return ()
    _require_ccw(subject, "subject", tolerance)
    _require_ccw(clipper, "clipper", tolerance)
    output = _dedupe_vertices(tuple(subject), tolerance)
    for index, edge_start in enumerate(clipper):
        edge_end = clipper[(index + 1) % len(clipper)]
        input_points = output
        output = []
        if not input_points:
            break
        previous = input_points[-1]
        for current in input_points:
            current_inside = _inside(current, edge_start, edge_end, tolerance)
            previous_inside = _inside(previous, edge_start, edge_end, tolerance)
            if current_inside:
                if not previous_inside:
                    output.append(_line_intersection(previous, current, edge_start, edge_end, tolerance))
                output.append(current)
            elif previous_inside:
                output.append(_line_intersection(previous, current, edge_start, edge_end, tolerance))
            previous = current
        output = list(_dedupe_vertices(tuple(output), tolerance))
    if polygon_area(output) <= tolerance.area_abs_tol:
        return ()
    return tuple(output)


def convex_polygon_intersection(
    subject: tuple[Vec2, ...] | list[Vec2],
    clipper: tuple[Vec2, ...] | list[Vec2],
    tolerance: GeometryTolerance = DEFAULT_TOLERANCE,
) -> tuple[Vec2, ...]:
    return clip_convex_polygon(subject, clipper, tolerance)


def convex_polygon_intersection_area(
    subject: tuple[Vec2, ...] | list[Vec2],
    clipper: tuple[Vec2, ...] | list[Vec2],
    tolerance: GeometryTolerance = DEFAULT_TOLERANCE,
) -> float:
    return polygon_area(convex_polygon_intersection(subject, clipper, tolerance))


def circumcircle_candidate_may_overlap(
    cell_a: HexCell,
    cell_b: HexCell,
    tolerance: GeometryTolerance = DEFAULT_TOLERANCE,
) -> bool:
    distance = (cell_a.center - cell_b.center).norm()
    return distance <= cell_a.side_length + cell_b.side_length + tolerance.coordinate_abs_tol


def _require_ccw(vertices: tuple[Vec2, ...] | list[Vec2], label: str, tolerance: GeometryTolerance) -> None:
    if signed_polygon_area(vertices) <= tolerance.area_abs_tol:
        raise ValueError(f"{label} polygon must be counter-clockwise with positive area")


def _inside(point: Vec2, edge_start: Vec2, edge_end: Vec2, tolerance: GeometryTolerance) -> bool:
    edge = edge_end - edge_start
    rel = point - edge_start
    return edge.cross(rel) >= -tolerance.coordinate_abs_tol


def _line_intersection(a: Vec2, b: Vec2, c: Vec2, d: Vec2, tolerance: GeometryTolerance) -> Vec2:
    ab = b - a
    cd = d - c
    denominator = ab.cross(cd)
    if abs(denominator) <= tolerance.coordinate_abs_tol:
        return b
    t = (c - a).cross(cd) / denominator
    return Vec2(a.x + t * ab.x, a.y + t * ab.y)


def _dedupe_vertices(vertices: tuple[Vec2, ...], tolerance: GeometryTolerance) -> tuple[Vec2, ...]:
    deduped: list[Vec2] = []
    for vertex in vertices:
        if not deduped or (vertex - deduped[-1]).norm() > tolerance.coordinate_abs_tol:
            deduped.append(vertex)
    if len(deduped) > 1 and (deduped[0] - deduped[-1]).norm() <= tolerance.coordinate_abs_tol:
        deduped.pop()
    return tuple(deduped)


__all__ = [
    "circumcircle_candidate_may_overlap",
    "clip_convex_polygon",
    "convex_polygon_intersection",
    "convex_polygon_intersection_area",
    "polygon_area",
    "signed_polygon_area",
]
