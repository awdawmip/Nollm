from __future__ import annotations

from dataclasses import dataclass
from math import atan2, cos, hypot, pi, radians, sin, sqrt
from typing import Literal

Point = tuple[float, float]
Polygon = list[Point]
Denominator = Literal["source", "target", "union"]
Orientation = Literal["pointy", "flat"]

EPS = 1e-12


@dataclass(frozen=True, order=True)
class Axial:
    q: int
    r: int

    def to_cube(self) -> "Cube":
        return Cube(self.q, -self.q - self.r, self.r)


@dataclass(frozen=True, order=True)
class Cube:
    x: int
    y: int
    z: int

    def __post_init__(self) -> None:
        if self.x + self.y + self.z != 0:
            raise ValueError("cube coordinates must satisfy x + y + z == 0")

    def to_axial(self) -> Axial:
        return Axial(self.x, self.z)


@dataclass(frozen=True)
class LayerSpec:
    layer: int
    s0: float = 1.0
    beta: float = 2 ** 0.25
    theta_deg: float = 22.5
    origin: Point = (0.0, 0.0)
    translation: Point = (0.0, 0.0)
    orientation: Orientation = "pointy"
    finer_down: bool = True
    rotation_mod_deg: float | None = 60.0

    def __post_init__(self) -> None:
        if not isinstance(self.layer, int) or isinstance(self.layer, bool) or self.layer < 0:
            raise ValueError(f"layer must be a non-negative integer: {self.layer}")
        if not _is_number(self.s0) or self.s0 <= 0:
            raise ValueError("s0 must be positive")
        if not _is_number(self.beta) or self.beta <= 0:
            raise ValueError("beta must be positive")
        if not _is_number(self.theta_deg):
            raise ValueError("theta_deg must be numeric")
        if not isinstance(self.finer_down, bool):
            raise ValueError("finer_down must be a boolean")
        if self.orientation not in ("pointy", "flat"):
            raise ValueError("orientation must be 'pointy' or 'flat'")
        if self.rotation_mod_deg is not None and (
            not _is_number(self.rotation_mod_deg) or self.rotation_mod_deg <= 0
        ):
            raise ValueError("rotation_mod_deg must be positive")
        _require_point(self.origin, "origin")
        _require_point(self.translation, "translation")

    @property
    def side_length(self) -> float:
        exponent = -self.layer if self.finer_down else self.layer
        return float(self.s0 * (self.beta**exponent))

    @property
    def rotation_deg(self) -> float:
        rotation = self.layer * self.theta_deg
        if self.rotation_mod_deg is not None:
            rotation %= self.rotation_mod_deg
        return float(rotation)

    @property
    def rotation_rad(self) -> float:
        return radians(self.rotation_deg)

    @property
    def area(self) -> float:
        return regular_hex_area(self.side_length)


@dataclass(frozen=True)
class HexAddress:
    layer: int
    q: int
    r: int

    @property
    def axial(self) -> Axial:
        return Axial(self.q, self.r)

    def uri(self) -> str:
        return f"nollm://layer/{self.layer}/hex/{self.q}/{self.r}"


@dataclass(frozen=True)
class Coverage:
    source: HexAddress
    target: HexAddress
    intersection_area: float
    source_area: float
    target_area: float
    weight_source: float
    weight_target: float
    jaccard: float

    @property
    def source_share(self) -> float:
        return self.weight_source

    @property
    def target_share(self) -> float:
        return self.weight_target


@dataclass(frozen=True)
class LocalChart:
    seed: HexAddress
    layer_specs: dict[int, LayerSpec]
    source_radius: int = 1
    projection_radius: int = 2

    def cells_on_seed_layer(self) -> list[HexAddress]:
        _require_non_negative_radius(self.source_radius)
        cells = axial_disk(self.seed.axial, self.source_radius)
        return [HexAddress(self.seed.layer, cell.q, cell.r) for cell in cells]

    def project_seed_layer_to(self, target_layer_id: int) -> dict[HexAddress, list[Coverage]]:
        source_layer = self._layer_spec(self.seed.layer)
        target_layer = self._layer_spec(target_layer_id)
        return {
            cell: coverage_map(
                cell,
                source_layer,
                target_layer,
                search_radius=self.projection_radius,
            )
            for cell in self.cells_on_seed_layer()
        }

    def _layer_spec(self, layer_id: int) -> LayerSpec:
        try:
            return self.layer_specs[layer_id]
        except KeyError as exc:
            raise ValueError(f"missing layer spec for layer {layer_id}") from exc


@dataclass(frozen=True)
class SimilarityTransform:
    scale: float = 1.0
    rotation_rad: float = 0.0
    translation: Point = (0.0, 0.0)

    def apply(self, p: Point) -> Point:
        rotated = rotate_point((p[0] * self.scale, p[1] * self.scale), self.rotation_rad)
        return add_points(rotated, self.translation)

    def inverse(self) -> "SimilarityTransform":
        if abs(self.scale) <= EPS:
            raise ValueError("cannot invert a zero-scale similarity transform")
        inverse_scale = 1.0 / self.scale
        inverse_rotation = -self.rotation_rad
        inverse_translation = rotate_point(
            (-self.translation[0] * inverse_scale, -self.translation[1] * inverse_scale),
            inverse_rotation,
        )
        return SimilarityTransform(inverse_scale, inverse_rotation, inverse_translation)

    def compose(self, after: "SimilarityTransform") -> "SimilarityTransform":
        scale = self.scale * after.scale
        rotation = self.rotation_rad + after.rotation_rad
        translation = after.apply(self.translation)
        return SimilarityTransform(scale, rotation, translation)


@dataclass(frozen=True)
class SimilarityFromTwoPoints:
    transform: SimilarityTransform
    residual: float


CUBE_DIRECTIONS: tuple[Cube, ...] = (
    Cube(1, -1, 0),
    Cube(1, 0, -1),
    Cube(0, 1, -1),
    Cube(-1, 1, 0),
    Cube(-1, 0, 1),
    Cube(0, -1, 1),
)


def cube_add(a: Cube, b: Cube) -> Cube:
    return Cube(a.x + b.x, a.y + b.y, a.z + b.z)


def cube_scale(a: Cube, k: int) -> Cube:
    return Cube(a.x * k, a.y * k, a.z * k)


def cube_neighbor(c: Cube, direction: int) -> Cube:
    return cube_add(c, CUBE_DIRECTIONS[direction % 6])


def axial_neighbor(a: Axial, direction: int) -> Axial:
    return cube_neighbor(a.to_cube(), direction).to_axial()


def cube_distance(a: Cube, b: Cube) -> int:
    return max(abs(a.x - b.x), abs(a.y - b.y), abs(a.z - b.z))


def axial_distance(a: Axial, b: Axial) -> int:
    return cube_distance(a.to_cube(), b.to_cube())


def cube_ring(center: Cube, radius: int) -> list[Cube]:
    _require_non_negative_radius(radius)
    if radius == 0:
        return [center]
    cells: list[Cube] = []
    current = cube_add(center, cube_scale(CUBE_DIRECTIONS[4], radius))
    for direction in range(6):
        for _ in range(radius):
            cells.append(current)
            current = cube_neighbor(current, direction)
    return cells


def axial_ring(center: Axial, radius: int) -> list[Axial]:
    return [cell.to_axial() for cell in cube_ring(center.to_cube(), radius)]


def axial_disk(center: Axial, radius: int) -> list[Axial]:
    _require_non_negative_radius(radius)
    cells: list[Axial] = []
    for dq in range(-radius, radius + 1):
        min_dr = max(-radius, -dq - radius)
        max_dr = min(radius, -dq + radius)
        for dr in range(min_dr, max_dr + 1):
            cells.append(Axial(center.q + dq, center.r + dr))
    return sorted(cells)


def cube_round(x: float, y: float, z: float) -> Cube:
    rx = round(x)
    ry = round(y)
    rz = round(z)

    x_diff = abs(rx - x)
    y_diff = abs(ry - y)
    z_diff = abs(rz - z)

    if x_diff > y_diff and x_diff > z_diff:
        rx = -ry - rz
    elif y_diff > z_diff:
        ry = -rx - rz
    else:
        rz = -rx - ry
    return Cube(int(rx), int(ry), int(rz))


def axial_round(q: float, r: float) -> Axial:
    return cube_round(q, -q - r, r).to_axial()


def rotate_point(p: Point, angle_rad: float) -> Point:
    c = cos(angle_rad)
    s = sin(angle_rad)
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


def add_points(a: Point, b: Point) -> Point:
    return (a[0] + b[0], a[1] + b[1])


def sub_points(a: Point, b: Point) -> Point:
    return (a[0] - b[0], a[1] - b[1])


def axial_to_local_xy(a: Axial, side_length: float, orientation: Orientation = "pointy") -> Point:
    if orientation == "pointy":
        return (
            side_length * sqrt(3) * (a.q + a.r / 2.0),
            side_length * 1.5 * a.r,
        )
    if orientation == "flat":
        return (
            side_length * 1.5 * a.q,
            side_length * sqrt(3) * (a.r + a.q / 2.0),
        )
    raise ValueError("orientation must be 'pointy' or 'flat'")


def local_xy_to_axial_fractional(
    p: Point,
    side_length: float,
    orientation: Orientation = "pointy",
) -> tuple[float, float]:
    if abs(side_length) <= EPS:
        raise ValueError("side_length must be non-zero")
    if orientation == "pointy":
        q = (sqrt(3) / 3.0 * p[0] - p[1] / 3.0) / side_length
        r = (2.0 / 3.0 * p[1]) / side_length
        return (q, r)
    if orientation == "flat":
        q = (2.0 / 3.0 * p[0]) / side_length
        r = (-p[0] / 3.0 + sqrt(3) / 3.0 * p[1]) / side_length
        return (q, r)
    raise ValueError("orientation must be 'pointy' or 'flat'")


def axial_to_world(a: Axial, layer: LayerSpec) -> Point:
    local = axial_to_local_xy(a, layer.side_length, layer.orientation)
    rotated = rotate_point(local, layer.rotation_rad)
    return add_points(add_points(layer.origin, layer.translation), rotated)


def world_to_axial_fractional(p: Point, layer: LayerSpec) -> tuple[float, float]:
    translated = sub_points(sub_points(p, layer.origin), layer.translation)
    local = rotate_point(translated, -layer.rotation_rad)
    return local_xy_to_axial_fractional(local, layer.side_length, layer.orientation)


def world_to_axial(p: Point, layer: LayerSpec) -> Axial:
    q, r = world_to_axial_fractional(p, layer)
    return axial_round(q, r)


def regular_hex_area(side_length: float) -> float:
    if not _is_number(side_length) or side_length <= 0:
        raise ValueError("side_length must be positive")
    return 3.0 * sqrt(3) / 2.0 * side_length * side_length


def hex_polygon(
    center: Point,
    side_length: float,
    rotation_rad: float = 0.0,
    orientation: Orientation = "pointy",
) -> Polygon:
    _require_point(center, "center")
    if not _is_number(side_length) or side_length <= 0:
        raise ValueError("side_length must be positive")
    if orientation == "pointy":
        vertex_offset = pi / 6.0
    elif orientation == "flat":
        vertex_offset = 0.0
    else:
        raise ValueError("orientation must be 'pointy' or 'flat'")
    return [
        (
            center[0] + side_length * cos(rotation_rad + vertex_offset + i * pi / 3.0),
            center[1] + side_length * sin(rotation_rad + vertex_offset + i * pi / 3.0),
        )
        for i in range(6)
    ]


def hex_cell_polygon(a: Axial, layer: LayerSpec) -> Polygon:
    return hex_polygon(
        axial_to_world(a, layer),
        layer.side_length,
        layer.rotation_rad,
        layer.orientation,
    )


def polygon_area(poly: list[Point]) -> float:
    if len(poly) < 3:
        return 0.0
    total = 0.0
    for index, point in enumerate(poly):
        nxt = poly[(index + 1) % len(poly)]
        total += point[0] * nxt[1] - nxt[0] * point[1]
    return abs(total) / 2.0


def convex_polygon_intersection(subject: list[Point], clip: list[Point]) -> Polygon:
    if len(subject) < 3 or len(clip) < 3:
        return []

    output = list(subject)
    clip_sign = 1.0 if _signed_polygon_area(clip) >= 0 else -1.0

    for index, edge_start in enumerate(clip):
        edge_end = clip[(index + 1) % len(clip)]
        input_points = output
        output = []
        if not input_points:
            break
        previous = input_points[-1]
        for current in input_points:
            current_inside = _inside_clip_edge(current, edge_start, edge_end, clip_sign)
            previous_inside = _inside_clip_edge(previous, edge_start, edge_end, clip_sign)
            if current_inside:
                if not previous_inside:
                    output.append(_line_intersection(previous, current, edge_start, edge_end))
                output.append(current)
            elif previous_inside:
                output.append(_line_intersection(previous, current, edge_start, edge_end))
            previous = current
    return output


def polygon_intersection_area(a: list[Point], b: list[Point]) -> float:
    return polygon_area(convex_polygon_intersection(a, b))


def hex_overlap(
    source: HexAddress,
    source_layer: LayerSpec,
    target: HexAddress,
    target_layer: LayerSpec,
) -> Coverage:
    _require_matching_layer(source, source_layer, "source")
    _require_matching_layer(target, target_layer, "target")
    source_poly = hex_cell_polygon(source.axial, source_layer)
    target_poly = hex_cell_polygon(target.axial, target_layer)
    intersection_area = polygon_intersection_area(source_poly, target_poly)
    if intersection_area <= EPS:
        intersection_area = 0.0
    source_area = source_layer.area
    target_area = target_layer.area
    union_area = source_area + target_area - intersection_area
    return Coverage(
        source=source,
        target=target,
        intersection_area=intersection_area,
        source_area=source_area,
        target_area=target_area,
        weight_source=intersection_area / source_area if source_area > EPS else 0.0,
        weight_target=intersection_area / target_area if target_area > EPS else 0.0,
        jaccard=intersection_area / union_area if union_area > EPS else 0.0,
    )


def coverage_weight(c: Coverage, denominator: Denominator = "source") -> float:
    if denominator == "source":
        return c.weight_source
    if denominator == "target":
        return c.weight_target
    if denominator == "union":
        return c.jaccard
    raise ValueError(f"unsupported denominator: {denominator}")


def coverage_map(
    source: HexAddress,
    source_layer: LayerSpec,
    target_layer: LayerSpec,
    search_radius: int = 2,
    min_weight: float = 0.0,
    denominator: Denominator = "source",
) -> list[Coverage]:
    _require_non_negative_radius(search_radius)
    if not _is_number(min_weight) or min_weight < 0:
        raise ValueError("min_weight must be non-negative")
    _require_matching_layer(source, source_layer, "source")
    source_center = axial_to_world(source.axial, source_layer)
    q, r = world_to_axial_fractional(source_center, target_layer)
    candidate_center = axial_round(q, r)
    candidates = axial_disk(candidate_center, search_radius)
    coverages = [
        hex_overlap(
            source,
            source_layer,
            HexAddress(target_layer.layer, candidate.q, candidate.r),
            target_layer,
        )
        for candidate in candidates
    ]
    filtered = [
        coverage
        for coverage in coverages
        if coverage_weight(coverage, denominator) > min_weight
    ]
    return sorted(
        filtered,
        key=lambda item: (
            -coverage_weight(item, denominator),
            item.target.q,
            item.target.r,
        ),
    )


def similarity_from_two_points(
    src_a: Point,
    src_b: Point,
    dst_a: Point,
    dst_b: Point,
) -> SimilarityFromTwoPoints:
    src_delta = sub_points(src_b, src_a)
    dst_delta = sub_points(dst_b, dst_a)
    src_length = hypot(src_delta[0], src_delta[1])
    dst_length = hypot(dst_delta[0], dst_delta[1])
    if src_length <= EPS:
        raise ValueError("cannot build similarity from degenerate source points")
    scale = dst_length / src_length
    rotation = atan2(dst_delta[1], dst_delta[0]) - atan2(src_delta[1], src_delta[0])
    scaled_rotated_origin = rotate_point((src_a[0] * scale, src_a[1] * scale), rotation)
    translation = sub_points(dst_a, scaled_rotated_origin)
    transform = SimilarityTransform(scale, rotation, translation)
    residual = hypot(
        transform.apply(src_b)[0] - dst_b[0],
        transform.apply(src_b)[1] - dst_b[1],
    )
    return SimilarityFromTwoPoints(transform, residual)


def default_layer_specs(
    max_layer: int,
    s0: float = 1.0,
    beta: float = 2 ** 0.25,
    theta_deg: float = 22.5,
    origin: Point = (0.0, 0.0),
    orientation: Orientation = "pointy",
) -> dict[int, LayerSpec]:
    if not isinstance(max_layer, int) or isinstance(max_layer, bool) or max_layer < 0:
        raise ValueError("max_layer must be a non-negative integer")
    return {
        layer: LayerSpec(
            layer=layer,
            s0=s0,
            beta=beta,
            theta_deg=theta_deg,
            origin=origin,
            orientation=orientation,
        )
        for layer in range(max_layer + 1)
    }


def _require_non_negative_radius(radius: int) -> None:
    if not isinstance(radius, int) or isinstance(radius, bool) or radius < 0:
        raise ValueError(f"radius must be a non-negative integer: {radius}")


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _require_point(value: Point, label: str) -> None:
    if not isinstance(value, tuple) or len(value) != 2:
        raise ValueError(f"{label} must be a 2-point numeric tuple")
    if not _is_number(value[0]) or not _is_number(value[1]):
        raise ValueError(f"{label} must be a 2-point numeric tuple")


def _require_matching_layer(address: HexAddress, layer: LayerSpec, label: str) -> None:
    if address.layer != layer.layer:
        raise ValueError(f"{label} address layer does not match layer spec")


def _signed_polygon_area(poly: list[Point]) -> float:
    total = 0.0
    for index, point in enumerate(poly):
        nxt = poly[(index + 1) % len(poly)]
        total += point[0] * nxt[1] - nxt[0] * point[1]
    return total / 2.0


def _inside_clip_edge(point: Point, edge_start: Point, edge_end: Point, clip_sign: float) -> bool:
    edge = sub_points(edge_end, edge_start)
    rel = sub_points(point, edge_start)
    cross = edge[0] * rel[1] - edge[1] * rel[0]
    return clip_sign * cross >= -EPS


def _line_intersection(a: Point, b: Point, c: Point, d: Point) -> Point:
    ab = sub_points(b, a)
    cd = sub_points(d, c)
    denominator = ab[0] * cd[1] - ab[1] * cd[0]
    if abs(denominator) <= EPS:
        return b
    ca = sub_points(c, a)
    t = (ca[0] * cd[1] - ca[1] * cd[0]) / denominator
    return (a[0] + t * ab[0], a[1] + t * ab[1])


__all__ = [
    "EPS",
    "Axial",
    "Cube",
    "LayerSpec",
    "HexAddress",
    "Coverage",
    "LocalChart",
    "SimilarityTransform",
    "SimilarityFromTwoPoints",
    "Point",
    "Polygon",
    "Denominator",
    "Orientation",
    "CUBE_DIRECTIONS",
    "cube_add",
    "cube_scale",
    "cube_neighbor",
    "axial_neighbor",
    "cube_distance",
    "axial_distance",
    "cube_ring",
    "axial_ring",
    "axial_disk",
    "cube_round",
    "axial_round",
    "rotate_point",
    "add_points",
    "sub_points",
    "axial_to_local_xy",
    "local_xy_to_axial_fractional",
    "axial_to_world",
    "world_to_axial_fractional",
    "world_to_axial",
    "regular_hex_area",
    "hex_polygon",
    "hex_cell_polygon",
    "polygon_area",
    "convex_polygon_intersection",
    "polygon_intersection_area",
    "hex_overlap",
    "coverage_weight",
    "coverage_map",
    "similarity_from_two_points",
    "default_layer_specs",
]
