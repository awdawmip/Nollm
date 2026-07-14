from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json

from .fixed_point import Q16_ONE
from .geometry import GeometryAddress
from .kernel_registry import KernelRegistry
from .validation import exact_int, exact_mapping, exact_str


DEFAULT_PAGE_SIZE = 8
MAX_PAGE_SIZE = 256
MAX_COMPILED_SURFACE_ORDER = 8
Q32_ONE = 1 << 32
OBSERVATION_AREA_RATIO_Q32 = (
    4294967296, 6074001000, 8589934592, 12148002000, 17179869184,
    24296004000, 34359738368, 48592008000, 68719476736,
)


@dataclass(frozen=True)
class PhysicalFieldScope:
    profile_id: str
    chart_id: str
    physical_layers: tuple[int, ...]
    reference_layer: int
    phase_policy: str = "physical_layer_mod8"
    max_relative_layer_delta: int = 8

    def __post_init__(self) -> None:
        from .profiles import runtime_profile

        runtime_profile(self.profile_id)
        exact_str(self.chart_id, "chart_id")
        exact_int(self.reference_layer, "reference_layer")
        exact_str(self.phase_policy, "phase_policy")
        exact_int(self.max_relative_layer_delta, "max_relative_layer_delta")
        if type(self.physical_layers) is not tuple or any(type(layer) is not int for layer in self.physical_layers):
            raise TypeError("physical_layers must be an integer tuple")
        if not self.physical_layers or tuple(sorted(set(self.physical_layers))) != self.physical_layers:
            raise ValueError("physical_layers must be a non-empty canonical set")
        if self.reference_layer not in self.physical_layers:
            raise ValueError("reference_layer must be in physical_layers")
        if self.max_relative_layer_delta < 0:
            raise ValueError("max_relative_layer_delta must be non-negative")
        if any(abs(layer - self.reference_layer) > self.max_relative_layer_delta for layer in self.physical_layers):
            raise ValueError("physical layer span is unsupported")

    @property
    def identity(self) -> str:
        payload = json.dumps(self.to_mapping(), sort_keys=True, separators=(",", ":")).encode("ascii")
        return sha256(payload).hexdigest()

    def contains(self, address: GeometryAddress) -> bool:
        if type(address) is not GeometryAddress:
            raise TypeError("address must be GeometryAddress")
        return (
            address.profile_id == self.profile_id
            and address.chart_id == self.chart_id
            and address.layer in self.physical_layers
        )

    def to_mapping(self) -> dict[str, object]:
        return {
            "profile_id": self.profile_id,
            "chart_id": self.chart_id,
            "physical_layers": list(self.physical_layers),
            "reference_layer": self.reference_layer,
            "phase_policy": self.phase_policy,
            "max_relative_layer_delta": self.max_relative_layer_delta,
        }

    @classmethod
    def from_mapping(cls, value: object) -> "PhysicalFieldScope":
        item = exact_mapping(value, frozenset({"profile_id", "chart_id", "physical_layers", "reference_layer", "phase_policy", "max_relative_layer_delta"}), "PhysicalFieldScope")
        layers = item["physical_layers"]
        if type(layers) is not list:
            raise TypeError("physical_layers must be an array")
        return cls(exact_str(item["profile_id"], "profile_id"), exact_str(item["chart_id"], "chart_id"), tuple(layers), exact_int(item["reference_layer"], "reference_layer"), exact_str(item["phase_policy"], "phase_policy"), exact_int(item["max_relative_layer_delta"], "max_relative_layer_delta"))


@dataclass(frozen=True, order=True)
class SurfaceGridSpec:
    reference_physical_layer: int
    aggregation_order: int
    observation_phase: int
    observation_area_ratio_q32: int


@dataclass(frozen=True, order=True)
class SurfaceAggregateAddress:
    profile_id: str
    chart_id: str
    field_scope_id: str
    reference_physical_layer: int
    aggregation_order: int
    q: int
    r: int
    observation_phase: int

    def __post_init__(self) -> None:
        from .profiles import runtime_profile

        runtime_profile(self.profile_id)
        for name in ("chart_id", "field_scope_id"):
            exact_str(getattr(self, name), name)
        for name in ("reference_physical_layer", "aggregation_order", "q", "r", "observation_phase"):
            exact_int(getattr(self, name), name)
        _require_order(self.aggregation_order)
        if not 0 <= self.observation_phase < 8:
            raise ValueError("observation_phase must be between 0 and 7")

    def stable_key(self) -> tuple[str, str, str, int, int, int, int, int]:
        return self.profile_id, self.chart_id, self.field_scope_id, self.reference_physical_layer, self.aggregation_order, self.q, self.r, self.observation_phase

    def to_mapping(self) -> dict[str, object]:
        return {
            "profile_id": self.profile_id, "chart_id": self.chart_id,
            "field_scope_id": self.field_scope_id,
            "reference_physical_layer": self.reference_physical_layer,
            "aggregation_order": self.aggregation_order, "q": self.q, "r": self.r,
            "observation_phase": self.observation_phase,
        }

    @classmethod
    def from_mapping(cls, value: object) -> "SurfaceAggregateAddress":
        keys = frozenset({"profile_id", "chart_id", "field_scope_id", "reference_physical_layer", "aggregation_order", "q", "r", "observation_phase"})
        item = exact_mapping(value, keys, "SurfaceAggregateAddress")
        return cls(exact_str(item["profile_id"], "profile_id"), exact_str(item["chart_id"], "chart_id"), exact_str(item["field_scope_id"], "field_scope_id"), exact_int(item["reference_physical_layer"], "reference_physical_layer"), exact_int(item["aggregation_order"], "aggregation_order"), exact_int(item["q"], "q"), exact_int(item["r"], "r"), exact_int(item["observation_phase"], "observation_phase"))


@dataclass(frozen=True)
class SurfaceCellProjection:
    address: SurfaceAggregateAddress
    grid: SurfaceGridSpec
    native_atom_count: int
    aggregate_atom_count: int
    physical_source_cell_count: int
    aggregate_mass_q16: int
    density_q16: int
    source_cells: tuple[GeometryAddress, ...]
    has_deeper_locality: bool
    has_bridge_endpoint: bool
    truncated: bool = False
    overflow: bool = False

    @property
    def order(self) -> int:
        return self.address.aggregation_order


@dataclass(frozen=True)
class SurfaceOrderInfo:
    scope: PhysicalFieldScope
    grid: SurfaceGridSpec
    occupied_cell_count: int
    page_count_hint: int
    native_atom_count: int
    aggregate_mass_q16: int
    coverage_residual_q16: int
    max_descent_depth: int
    overflow: bool = False

    @property
    def order(self) -> int:
        return self.grid.aggregation_order


@dataclass(frozen=True)
class SurfacePage:
    scope: PhysicalFieldScope
    grid: SurfaceGridSpec
    cells: tuple[SurfaceCellProjection, ...]
    has_more: bool
    next_after: SurfaceAggregateAddress | None


@dataclass(frozen=True)
class CoverageDescentCell:
    projection: SurfaceCellProjection
    coverage_weight_q16: int
    flags: tuple[str, ...]


@dataclass(frozen=True)
class CoverageDescentPage:
    scope: PhysicalFieldScope
    parent_address: SurfaceAggregateAddress
    cells: tuple[CoverageDescentCell, ...]
    has_more: bool
    next_after: SurfaceAggregateAddress | None


@dataclass(frozen=True)
class _SurfaceRecord:
    projection: SurfaceCellProjection
    members: tuple[tuple[SurfaceAggregateAddress, int, tuple[str, ...]], ...]


def build_surface_orders(
    scope: PhysicalFieldScope,
    max_order: int,
    occupancy: dict[GeometryAddress, int],
    bridge_endpoints: frozenset[GeometryAddress],
    registry: KernelRegistry,
) -> tuple[tuple[_SurfaceRecord, ...], ...]:
    _require_order(max_order)
    native = {address: count for address, count in occupancy.items() if scope.contains(address)}
    grouped_zero: dict[tuple[int, int], dict[GeometryAddress, tuple[int, int, int]]] = {}
    for address in sorted(native, key=lambda item: item.stable_key()):
        projected, _residual = _physical_to_reference(address, scope.reference_layer, registry)
        distributed = _distribute_mass(native[address] * Q16_ONE, tuple(weight for _q, _r, weight in projected))
        count_owner = max(projected, key=lambda item: (item[2], -item[0], -item[1]))[:2]
        for (q, r, weight), mass in zip(projected, distributed):
            grouped_zero.setdefault((q, r), {})[address] = (weight, mass, native[address] if (q, r) == count_owner else 0)
    order_zero = []
    for (q, r), source_map in sorted(grouped_zero.items()):
        sources = tuple(sorted(source_map, key=lambda item: item.stable_key()))
        aggregate_count = sum(source_map[source][2] for source in sources)
        native_count = sum(native[source] for source in sources if source.layer == scope.reference_layer and (source.q, source.r) == (q, r))
        aggregate_mass = sum(source_map[source][1] for source in sources)
        address = _surface_address(scope, 0, q, r)
        order_zero.append(_SurfaceRecord(_projection(scope, address, native_count, aggregate_count, aggregate_mass, sources, False, any(source in bridge_endpoints for source in sources)), ()))
    orders: list[tuple[_SurfaceRecord, ...]] = [tuple(order_zero)]
    for order in range(1, max_order + 1):
        lower = orders[-1]
        lower_by_address = {record.projection.address: record for record in lower}
        grouped: dict[SurfaceAggregateAddress, dict[SurfaceAggregateAddress, tuple[int, tuple[str, ...], int]]] = {}
        for record in lower:
            source = GeometryAddress(scope.profile_id, scope.chart_id, scope.reference_layer - order + 1, record.projection.address.q, record.projection.address.r)
            targets = registry.expand_coverage(source, "coverage_up")
            distributed = _distribute_mass(record.projection.aggregate_mass_q16, tuple(weight for _target, weight in targets))
            for (physical_target, weight), mass in zip(targets, distributed):
                q, r = physical_target.q, physical_target.r
                flags = ("physical_overlap_projection", "translation_covariant")
                target = _surface_address(scope, order, q, r)
                grouped.setdefault(target, {})[record.projection.address] = (weight, flags, mass)
        records = []
        for target, edge_map in sorted(grouped.items(), key=lambda item: item[0].stable_key()):
            members = tuple((address, edge_map[address][0], edge_map[address][1]) for address in sorted(edge_map, key=lambda item: item.stable_key()))
            source_cells = tuple(sorted({source for address, _weight, _flags in members for source in lower_by_address[address].projection.source_cells}, key=lambda item: item.stable_key()))
            aggregate_count = sum(lower_by_address[address].projection.aggregate_atom_count for address, _weight, _flags in members)
            aggregate_mass = sum(edge_map[address][2] for address, _weight, _flags in members)
            records.append(_SurfaceRecord(_projection(scope, target, 0, aggregate_count, aggregate_mass, source_cells, True, any(source in bridge_endpoints for source in source_cells)), members))
        orders.append(tuple(records))
    return tuple(orders)


def order_info(scope: PhysicalFieldScope, records: tuple[_SurfaceRecord, ...], order: int) -> SurfaceOrderInfo:
    source_cells = {source for record in records for source in record.projection.source_cells}
    native_atom_count = sum(max(record.projection.native_atom_count, 0) for record in records) if order == 0 else len(source_cells)
    return SurfaceOrderInfo(scope, _grid(scope, order), len(records), (len(records) + DEFAULT_PAGE_SIZE - 1) // DEFAULT_PAGE_SIZE, native_atom_count, sum(record.projection.aggregate_mass_q16 for record in records), 0, order)


def surface_page(scope: PhysicalFieldScope, order: int, records: tuple[_SurfaceRecord, ...], after: SurfaceAggregateAddress | None, limit: int) -> SurfacePage:
    _require_page(scope, order, after, limit)
    selected = records if after is None else tuple(record for record in records if record.projection.address.stable_key() > after.stable_key())
    page_records = selected[:limit]
    has_more = len(selected) > limit
    return SurfacePage(scope, _grid(scope, order), tuple(record.projection for record in page_records), has_more, page_records[-1].projection.address if has_more and page_records else None)


def descent_page(scope: PhysicalFieldScope, parent_address: SurfaceAggregateAddress, orders: tuple[tuple[_SurfaceRecord, ...], ...], after: SurfaceAggregateAddress | None, limit: int) -> CoverageDescentPage:
    parent_order = parent_address.aggregation_order
    if not 1 <= parent_order <= MAX_COMPILED_SURFACE_ORDER:
        raise ValueError("parent Surface order must be between 1 and 8")
    _require_address(scope, parent_order, parent_address, "parent_address")
    _require_page(scope, parent_order - 1, after, limit)
    parent = next((record for record in orders[parent_order] if record.projection.address == parent_address), None)
    if parent is None:
        raise KeyError("surface parent is not occupied")
    lower = {record.projection.address: record for record in orders[parent_order - 1]}
    cells = tuple(CoverageDescentCell(lower[address].projection, weight, flags) for address, weight, flags in parent.members if address in lower and (after is None or address.stable_key() > after.stable_key()))
    page_cells = cells[:limit]
    has_more = len(cells) > limit
    return CoverageDescentPage(scope, parent_address, page_cells, has_more, page_cells[-1].projection.address if has_more and page_cells else None)


def _projection(scope, address, native_count, aggregate_count, mass, sources, deeper, bridge):
    area = OBSERVATION_AREA_RATIO_Q32[address.aggregation_order]
    density = mass * Q32_ONE // area
    return SurfaceCellProjection(address, _grid(scope, address.aggregation_order), native_count, aggregate_count, len(sources), mass, density, sources, deeper, bridge)


def _grid(scope: PhysicalFieldScope, order: int) -> SurfaceGridSpec:
    return SurfaceGridSpec(scope.reference_layer, order, (scope.reference_layer - order) % 8, OBSERVATION_AREA_RATIO_Q32[order])


def _surface_address(scope: PhysicalFieldScope, order: int, q: int, r: int) -> SurfaceAggregateAddress:
    return SurfaceAggregateAddress(scope.profile_id, scope.chart_id, scope.identity, scope.reference_layer, order, q, r, (scope.reference_layer - order) % 8)


def _physical_to_reference(address: GeometryAddress, reference_layer: int, registry: KernelRegistry) -> tuple[tuple[tuple[int, int, int], ...], int]:
    frontier = {address: Q16_ONE}
    layer = address.layer
    while layer > reference_layer:
        frontier = _project_frontier(frontier, registry, "coverage_up")
        layer -= 1
    while layer < reference_layer:
        frontier = _project_frontier(frontier, registry, "coverage_down")
        layer += 1
    ordered = tuple((cell.q, cell.r, weight) for cell, weight in sorted(frontier.items(), key=lambda item: item[0].stable_key()))
    return ordered, Q16_ONE - sum(weight for _q, _r, weight in ordered)


def _project_frontier(frontier: dict[GeometryAddress, int], registry: KernelRegistry, direction: str) -> dict[GeometryAddress, int]:
    projected: dict[GeometryAddress, int] = {}
    for source, source_mass in sorted(frontier.items(), key=lambda item: item[0].stable_key()):
        targets = registry.expand_coverage(source, direction)
        masses = _distribute_mass(source_mass, tuple(weight for _target, weight in targets))
        for (target, _weight), mass in zip(targets, masses):
            projected[target] = projected.get(target, 0) + mass
    return projected


def _distribute_mass(mass: int, weights: tuple[int, ...]) -> tuple[int, ...]:
    if mass < 0 or not weights or any(weight <= 0 for weight in weights):
        raise ValueError("surface mass distribution is invalid")
    total = sum(weights)
    output = [mass * weight // total for weight in weights]
    order = sorted(range(len(weights)), key=lambda index: (-((mass * weights[index]) % total), index))
    for index in order[: mass - sum(output)]:
        output[index] += 1
    return tuple(output)


def _require_order(order: int) -> None:
    if type(order) is not int or not 0 <= order <= MAX_COMPILED_SURFACE_ORDER:
        raise ValueError("surface order must be between 0 and 8")


def _require_page(scope: PhysicalFieldScope, order: int, after: SurfaceAggregateAddress | None, limit: int) -> None:
    _require_order(order)
    if type(limit) is not int or not 1 <= limit <= MAX_PAGE_SIZE:
        raise ValueError("surface page limit is out of bounds")
    if after is not None:
        _require_address(scope, order, after, "after")


def _require_address(scope: PhysicalFieldScope, order: int, address: object, name: str) -> None:
    if type(address) is not SurfaceAggregateAddress:
        raise TypeError(f"{name} must be SurfaceAggregateAddress")
    if (address.profile_id, address.chart_id, address.field_scope_id, address.reference_physical_layer, address.aggregation_order) != (scope.profile_id, scope.chart_id, scope.identity, scope.reference_layer, order):
        raise ValueError(f"{name} does not belong to the requested Surface order")
