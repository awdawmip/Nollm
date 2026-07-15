from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_EVEN, localcontext
from functools import lru_cache

from .fixed_point import Q16_ONE
from .geometry import GeometryAddress
from .profiles import DEFAULT_PROFILE_ID, GEOMETRY_CONTRACT_VERSION


_PI = Decimal("3.141592653589793238462643383279502884197169399375105820974944592307816406286208998628034825")
_MIN_COORDINATE = -(1 << 63)
_MAX_COORDINATE = (1 << 63) - 1
_MIN_LAYER = -64
_MAX_LAYER = 64
_BASE_PRECISION = 96
_GUARD_DIGITS = 72
_POSITIVE_AREA = Decimal("1e-70")
_PROPAGATION_SHARE_THRESHOLD = Decimal("1e-70")
_ADJACENT_CANDIDATE_RADIUS = 4
_VALIDATION_RADIUS = 6
_CANDIDATE_STRATEGY = "nearest_axial_radius4_validated_by_radius6"
_ORACLE_CONTRACT_ID = "nollm_translation_normalized_independent_oracles_v1"


class UnsupportedPhysicalCoverage(ValueError):
    """The requested address is outside the explicit physical contract."""


class AmbiguousPhysicalCoverage(ValueError):
    """The physical partition could not be certified before quantization."""


@dataclass(frozen=True, order=True)
class PhysicalCoverageMember:
    target: GeometryAddress
    weight_q16: int
    intersection_area: str
    source_share: str
    target_share: str
    numeric_error_bound: str
    ambiguous: bool
    classification: str
    q16_rounding_residual: int

    @property
    def quantization_residual_q16(self) -> int:
        return self.q16_rounding_residual


@dataclass(frozen=True)
class PhysicalCoverageExpansion:
    source: GeometryAddress
    direction: str
    members: tuple[PhysicalCoverageMember, ...]
    raw_source_share_sum: str
    raw_partition_residual: str
    candidate_window_residual: str
    threshold_residual: str
    numeric_error_bound: str
    ambiguous: bool
    q16_sum: int
    q16_rounding_residual: int
    candidate_radius: int
    candidate_strategy: str
    coordinate_contract_id: str
    oracle_contract_id: str

    @property
    def sum_weight_q16(self) -> int:
        return self.q16_sum

    @property
    def normalization_residual_q16(self) -> int:
        return Q16_ONE - self.q16_sum

    @property
    def max_quantization_residual_q16(self) -> int:
        return self.q16_rounding_residual

    def targets(self) -> tuple[tuple[GeometryAddress, int], ...]:
        if self.ambiguous:
            raise AmbiguousPhysicalCoverage("ambiguous physical coverage cannot propagate")
        return tuple((member.target, member.weight_q16) for member in self.members)


def expand_physical_coverage(source: GeometryAddress, direction: str) -> PhysicalCoverageExpansion:
    if type(source) is not GeometryAddress:
        raise TypeError("source must be GeometryAddress")
    if source.profile_id != DEFAULT_PROFILE_ID:
        raise UnsupportedPhysicalCoverage("physical coverage requires default_dream_v1")
    if source.chart_id != "default":
        raise UnsupportedPhysicalCoverage("physical coverage supports chart_id=default only")
    if source.phase is not None:
        raise UnsupportedPhysicalCoverage("physical coverage supports phase=null only")
    if direction not in ("coverage_up", "coverage_down"):
        raise UnsupportedPhysicalCoverage("physical coverage requires an adjacent-layer direction")
    target_layer = source.layer - 1 if direction == "coverage_up" else source.layer + 1
    if not _MIN_LAYER <= source.layer <= _MAX_LAYER or not _MIN_LAYER <= target_layer <= _MAX_LAYER:
        raise UnsupportedPhysicalCoverage("physical coverage layer is outside [-64,64]")
    if not _MIN_COORDINATE <= source.q <= _MAX_COORDINATE or not _MIN_COORDINATE <= source.r <= _MAX_COORDINATE:
        raise UnsupportedPhysicalCoverage("physical coverage q/r is outside signed-64")
    return _expand_cached(source, direction)


def clear_physical_coverage_cache() -> None:
    _expand_cached.cache_clear()
    _relative_constants.cache_clear()
    _source_vertices.cache_clear()


@lru_cache(maxsize=8192)
def _expand_cached(source: GeometryAddress, direction: str) -> PhysicalCoverageExpansion:
    target_layer = source.layer - 1 if direction == "coverage_up" else source.layer + 1
    precision = _precision_for(source)
    with localcontext() as context:
        context.prec = precision
        numeric_bound = Decimal(10) ** Decimal(-(precision - 24))
        source_polygon = _source_vertices(precision)
        source_area = _polygon_area(source_polygon)
        target_side, target_angle, target_sine, target_cosine = _relative_constants(target_layer - source.layer, precision)
        target_area = source_area * target_side * target_side
        fractional_q, fractional_r = _fractional_target(source, target_side, target_sine, target_cosine)
        center_q, center_r = _nearest_axial(fractional_q, fractional_r)

        overlaps: list[tuple[int, int, Decimal, Decimal, Decimal, bool]] = []
        raw_mass = Decimal(0)
        candidate_residual = Decimal(0)
        threshold_residual = Decimal(0)
        for target_q, target_r in _disk(center_q, center_r, _VALIDATION_RADIUS):
            residual_q = Decimal(target_q) - fractional_q
            residual_r = Decimal(target_r) - fractional_r
            axial_x, axial_y = _axial_world(residual_q, residual_r)
            center_x = target_side * (target_cosine * axial_x - target_sine * axial_y)
            center_y = target_side * (target_sine * axial_x + target_cosine * axial_y)
            target_polygon = _local_vertices(center_x, center_y, target_side, target_angle, precision)
            intersection = _intersection_area(source_polygon, target_polygon, numeric_bound)
            if intersection <= _POSITIVE_AREA:
                continue
            source_share = intersection / source_area
            target_share = intersection / target_area
            raw_mass += source_share
            outside_candidate = _hex_distance(target_q - center_q, target_r - center_r) > _ADJACENT_CANDIDATE_RADIUS
            if outside_candidate:
                candidate_residual += source_share
                continue
            below_threshold = source_share <= _PROPAGATION_SHARE_THRESHOLD
            if below_threshold:
                threshold_residual += source_share
            overlaps.append((target_q, target_r, intersection, source_share, target_share, below_threshold))

        partition_residual = abs(Decimal(1) - raw_mass)
        ambiguous = partition_residual > numeric_bound or candidate_residual > numeric_bound
        if ambiguous:
            raise AmbiguousPhysicalCoverage(
                "physical partition failed before Q16: "
                f"raw_source_share_sum={_decimal_text(raw_mass)} "
                f"raw_partition_residual={_decimal_text(partition_residual)} "
                f"candidate_window_residual={_decimal_text(candidate_residual)} "
                f"numeric_error_bound={_decimal_text(numeric_bound)}"
            )

        propagated = tuple(item for item in overlaps if not item[5])
        if not propagated:
            raise AmbiguousPhysicalCoverage("physical coverage produced no propagating overlap")
        weights = _quantize(tuple(item[3] for item in propagated))
        members = []
        max_rounding_residual = 0
        for item, weight in zip(propagated, weights):
            ideal = item[3] * Q16_ONE
            rounding_residual = int(abs(Decimal(weight) - ideal).to_integral_value(rounding=ROUND_CEILING))
            max_rounding_residual = max(max_rounding_residual, rounding_residual)
            members.append(
                PhysicalCoverageMember(
                    GeometryAddress(source.profile_id, source.chart_id, target_layer, item[0], item[1], source.phase),
                    weight,
                    _decimal_text(item[2]),
                    _decimal_text(item[3]),
                    _decimal_text(item[4]),
                    _decimal_text(numeric_bound),
                    False,
                    "core",
                    rounding_residual,
                )
            )
        ordered = tuple(sorted(members, key=lambda member: member.target.stable_key()))
        q16_sum = sum(member.weight_q16 for member in ordered)
        if q16_sum != Q16_ONE:
            raise AmbiguousPhysicalCoverage("Q16 adjustment did not preserve canonical mass")
        return PhysicalCoverageExpansion(
            source,
            direction,
            ordered,
            _decimal_text(raw_mass),
            _decimal_text(partition_residual),
            _decimal_text(candidate_residual),
            _decimal_text(threshold_residual),
            _decimal_text(numeric_bound),
            False,
            q16_sum,
            max_rounding_residual,
            _ADJACENT_CANDIDATE_RADIUS,
            _CANDIDATE_STRATEGY,
            GEOMETRY_CONTRACT_VERSION,
            _ORACLE_CONTRACT_ID,
        )


def _precision_for(source: GeometryAddress) -> int:
    coordinate_digits = max(len(str(abs(source.q))), len(str(abs(source.r))), 1)
    layer_digits = len(str(max(abs(source.layer), 1)))
    return max(_BASE_PRECISION, coordinate_digits + layer_digits + _GUARD_DIGITS)


def _quantize(shares: tuple[Decimal, ...]) -> tuple[int, ...]:
    scaled = tuple(share * Q16_ONE for share in shares)
    weights = [max(1, int(value.to_integral_value(rounding=ROUND_HALF_EVEN))) for value in scaled]
    delta = Q16_ONE - sum(weights)
    if delta > 0:
        for _ in range(delta):
            index = min(
                range(len(weights)),
                key=lambda item: (
                    abs(Decimal(weights[item] + 1) - scaled[item]) - abs(Decimal(weights[item]) - scaled[item]),
                    item,
                ),
            )
            weights[index] += 1
    elif delta < 0:
        for _ in range(-delta):
            candidates = tuple(index for index, weight in enumerate(weights) if weight > 1)
            if not candidates:
                raise AmbiguousPhysicalCoverage("Q16 adjustment would erase positive overlap")
            index = min(
                candidates,
                key=lambda item: (
                    abs(Decimal(weights[item] - 1) - scaled[item]) - abs(Decimal(weights[item]) - scaled[item]),
                    item,
                ),
            )
            weights[index] -= 1
    return tuple(weights)


@lru_cache(maxsize=256)
def _relative_constants(layer_delta: int, precision: int) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    with localcontext() as context:
        context.prec = precision
        side = Decimal(2).sqrt().sqrt() ** Decimal(-layer_delta)
        angle = _PI * Decimal(layer_delta) / Decimal(8)
        sine, cosine = _sin_cos(angle, precision)
        return +side, +angle, +sine, +cosine


@lru_cache(maxsize=16)
def _source_vertices(precision: int) -> tuple[tuple[Decimal, Decimal], ...]:
    with localcontext() as context:
        context.prec = precision
        return _local_vertices(Decimal(0), Decimal(0), Decimal(1), Decimal(0), precision)


def _fractional_target(
    source: GeometryAddress,
    target_side: Decimal,
    target_sine: Decimal,
    target_cosine: Decimal,
) -> tuple[Decimal, Decimal]:
    source_x, source_y = _axial_world(Decimal(source.q), Decimal(source.r))
    target_x = (target_cosine * source_x + target_sine * source_y) / target_side
    target_y = (-target_sine * source_x + target_cosine * source_y) / target_side
    target_r = Decimal(2) * target_y / 3
    target_q = target_x / Decimal(3).sqrt() - target_r / 2
    return +target_q, +target_r


def _axial_world(q: Decimal, r: Decimal) -> tuple[Decimal, Decimal]:
    return +(Decimal(3).sqrt() * (q + r / 2)), +(Decimal(3) * r / 2)


def _local_vertices(
    center_x: Decimal,
    center_y: Decimal,
    side: Decimal,
    angle: Decimal,
    precision: int,
) -> tuple[tuple[Decimal, Decimal], ...]:
    output = []
    for index in range(6):
        sine, cosine = _sin_cos(angle + _PI / 6 + _PI * Decimal(index) / 3, precision)
        output.append((+(center_x + side * cosine), +(center_y + side * sine)))
    return tuple(output)


def _sin_cos(angle: Decimal, precision: int) -> tuple[Decimal, Decimal]:
    with localcontext() as context:
        context.prec = precision
        angle %= _PI * 2
        if angle > _PI:
            angle -= _PI * 2
        sine = sine_term = angle
        cosine = cosine_term = Decimal(1)
        square = angle * angle
        stop = Decimal(10) ** Decimal(-(precision - 6))
        for index in range(1, precision + 24):
            sine_term *= -square / Decimal((2 * index) * (2 * index + 1))
            cosine_term *= -square / Decimal((2 * index - 1) * (2 * index))
            sine += sine_term
            cosine += cosine_term
            if abs(sine_term) < stop and abs(cosine_term) < stop:
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


def _hex_distance(q: int, r: int) -> int:
    return max(abs(q), abs(r), abs(q + r))


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


def _line_intersection(a, b, c, d, epsilon: Decimal):
    ab = b[0] - a[0], b[1] - a[1]
    cd = d[0] - c[0], d[1] - c[1]
    denominator = ab[0] * cd[1] - ab[1] * cd[0]
    if abs(denominator) < epsilon:
        return b
    factor = ((c[0] - a[0]) * cd[1] - (c[1] - a[1]) * cd[0]) / denominator
    return a[0] + factor * ab[0], a[1] + factor * ab[1]


def _intersection_area(subject, clipper, numeric_bound: Decimal) -> Decimal:
    output = list(subject)
    epsilon = numeric_bound / 1000
    for index, edge_start in enumerate(clipper):
        edge_end = clipper[(index + 1) % len(clipper)]
        points, output = output, []
        if not points:
            break
        previous = points[-1]
        for current in points:
            current_inside = _cross(edge_start, edge_end, current) >= -numeric_bound
            previous_inside = _cross(edge_start, edge_end, previous) >= -numeric_bound
            if current_inside:
                if not previous_inside:
                    output.append(_line_intersection(previous, current, edge_start, edge_end, epsilon))
                output.append(current)
            elif previous_inside:
                output.append(_line_intersection(previous, current, edge_start, edge_end, epsilon))
            previous = current
    return _polygon_area(output)


def _decimal_text(value: Decimal) -> str:
    return format(+value, "f")
