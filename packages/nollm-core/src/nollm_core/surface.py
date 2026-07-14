from __future__ import annotations

from dataclasses import dataclass

from .fixed_point import Q16_ONE
from .geometry import GeometryAddress
from .kernel_registry import KernelRegistry
from .validation import exact_int, exact_str


MAX_SURFACE_ORDER = 2
DEFAULT_PAGE_SIZE = 8
MAX_PAGE_SIZE = 256


@dataclass(frozen=True)
class SurfacePlane:
    profile_id: str
    chart_id: str
    phase: str | None
    base_layer: int

    def __post_init__(self) -> None:
        from .profiles import runtime_profile

        runtime_profile(self.profile_id)
        exact_str(self.chart_id, "chart_id")
        exact_int(self.base_layer, "base_layer")
        if self.phase is not None:
            exact_str(self.phase, "phase")

    def contains(self, address: GeometryAddress) -> bool:
        if type(address) is not GeometryAddress:
            raise TypeError("address must be GeometryAddress")
        return (
            address.profile_id,
            address.chart_id,
            address.phase,
            address.layer,
        ) == (self.profile_id, self.chart_id, self.phase, self.base_layer)


@dataclass(frozen=True)
class SurfaceCellProjection:
    order: int
    address: GeometryAddress
    native_occupancy_count: int
    aggregate_occupancy_count: int
    occupied_member_count: int
    aggregate_mass_q16: int
    density_q16: int
    dispersion_q16: int
    boundary_mass_q16: int
    has_deeper_locality: bool
    has_bridge_endpoint: bool


@dataclass(frozen=True)
class SurfaceOrderInfo:
    plane: SurfacePlane
    order: int
    occupied_cell_count: int
    page_count_hint: int
    native_atom_count: int
    aggregate_mass_q16: int
    max_descent_depth: int
    overflow: bool = False


@dataclass(frozen=True)
class SurfacePage:
    plane: SurfacePlane
    order: int
    cells: tuple[SurfaceCellProjection, ...]
    has_more: bool
    next_after: GeometryAddress | None


@dataclass(frozen=True)
class CoverageDescentCell:
    projection: SurfaceCellProjection
    coverage_weight_q16: int
    flags: tuple[str, ...]


@dataclass(frozen=True)
class CoverageDescentPage:
    plane: SurfacePlane
    parent_order: int
    parent_address: GeometryAddress
    cells: tuple[CoverageDescentCell, ...]
    has_more: bool
    next_after: GeometryAddress | None


@dataclass(frozen=True)
class _SurfaceRecord:
    projection: SurfaceCellProjection
    aggregate_mass_q16: int
    members: tuple[tuple[GeometryAddress, int, tuple[str, ...]], ...]


def build_surface_orders(
    plane: SurfacePlane,
    max_order: int,
    occupancy: dict[GeometryAddress, int],
    bridge_endpoints: frozenset[GeometryAddress],
    registry: KernelRegistry,
) -> tuple[tuple[_SurfaceRecord, ...], ...]:
    _require_order(max_order)
    native = {
        address: count
        for address, count in occupancy.items()
        if plane.contains(address)
    }
    order_zero = tuple(
        _SurfaceRecord(
            SurfaceCellProjection(
                0,
                address,
                count,
                count,
                1,
                count * Q16_ONE,
                min(Q16_ONE, count * Q16_ONE // 32),
                0,
                0,
                False,
                address in bridge_endpoints,
            ),
            count * Q16_ONE,
            (),
        )
        for address, count in sorted(native.items(), key=lambda item: item[0].stable_key())
    )
    orders: list[tuple[_SurfaceRecord, ...]] = [order_zero]
    template = registry.coverage_template(plane.profile_id, "coverage_up")
    for order in range(1, max_order + 1):
        grouped: dict[GeometryAddress, dict[GeometryAddress, tuple[int, tuple[str, ...]]]] = {}
        previous = orders[-1]
        for record in previous:
            source = record.projection.address
            entries_by_target = {
                GeometryAddress(
                    source.profile_id,
                    source.chart_id,
                    source.layer + entry.layer_delta,
                    source.q + entry.dq,
                    source.r + entry.dr,
                    source.phase,
                ): (entry.weight_q16, entry.flags)
                for entry in template.entries
            }
            for target, edge in entries_by_target.items():
                grouped.setdefault(target, {})[source] = edge
        records = []
        previous_by_address = {record.projection.address: record for record in previous}
        for target, member_edges in sorted(grouped.items(), key=lambda item: item[0].stable_key()):
            members = tuple(
                (member, member_edges[member][0], member_edges[member][1])
                for member in sorted(member_edges, key=lambda item: item.stable_key())
            )
            aggregate_count = sum(previous_by_address[member].projection.aggregate_occupancy_count for member, _weight, _flags in members)
            aggregate_mass = sum(
                previous_by_address[member].aggregate_mass_q16 * weight // Q16_ONE
                for member, weight, _flags in members
            )
            boundary_mass = sum(
                weight for _member, weight, flags in members if "boundary" in flags or "halo" in flags
            )
            max_distance = max((_hex_distance(member, target) for member, _weight, _flags in members), default=0)
            dispersion = 0 if max_distance == 0 else min(Q16_ONE, max_distance * Q16_ONE // (max_distance + 1))
            native_count = occupancy.get(target, 0)
            projection = SurfaceCellProjection(
                order,
                target,
                native_count,
                aggregate_count,
                len(members),
                aggregate_mass,
                min(Q16_ONE, aggregate_count * Q16_ONE // (32 * max(1, len(members)))),
                dispersion,
                min(Q16_ONE, boundary_mass),
                bool(members),
                target in bridge_endpoints,
            )
            records.append(_SurfaceRecord(projection, aggregate_mass, members))
        orders.append(tuple(records))
    return tuple(orders)


def order_info(plane: SurfacePlane, records: tuple[_SurfaceRecord, ...], order: int) -> SurfaceOrderInfo:
    native_atom_count = sum(record.projection.native_occupancy_count for record in records)
    return SurfaceOrderInfo(
        plane,
        order,
        len(records),
        (len(records) + DEFAULT_PAGE_SIZE - 1) // DEFAULT_PAGE_SIZE,
        native_atom_count,
        sum(record.aggregate_mass_q16 for record in records),
        order,
    )


def surface_page(
    plane: SurfacePlane,
    order: int,
    records: tuple[_SurfaceRecord, ...],
    after: GeometryAddress | None,
    limit: int,
) -> SurfacePage:
    _require_page(plane, order, after, limit)
    selected = _after(records, after)
    page_records = selected[:limit]
    has_more = len(selected) > limit
    return SurfacePage(
        plane,
        order,
        tuple(record.projection for record in page_records),
        has_more,
        page_records[-1].projection.address if has_more and page_records else None,
    )


def descent_page(
    plane: SurfacePlane,
    parent_order: int,
    parent_address: GeometryAddress,
    orders: tuple[tuple[_SurfaceRecord, ...], ...],
    after: GeometryAddress | None,
    limit: int,
) -> CoverageDescentPage:
    if type(parent_order) is not int or not 1 <= parent_order <= MAX_SURFACE_ORDER:
        raise ValueError("parent_order must be 1 or 2")
    _require_address_for_order(plane, parent_order, parent_address, "parent_address")
    _require_page(plane, parent_order - 1, after, limit)
    parent = next(
        (record for record in orders[parent_order] if record.projection.address == parent_address),
        None,
    )
    if parent is None:
        raise KeyError("surface parent is not occupied")
    lower = {record.projection.address: record for record in orders[parent_order - 1]}
    cells = tuple(
        CoverageDescentCell(lower[address].projection, weight, flags)
        for address, weight, flags in parent.members
        if address in lower and (after is None or address.stable_key() > after.stable_key())
    )
    page_cells = cells[:limit]
    has_more = len(cells) > limit
    return CoverageDescentPage(
        plane,
        parent_order,
        parent_address,
        page_cells,
        has_more,
        page_cells[-1].projection.address if has_more and page_cells else None,
    )


def _after(records: tuple[_SurfaceRecord, ...], after: GeometryAddress | None) -> tuple[_SurfaceRecord, ...]:
    if after is None:
        return records
    return tuple(record for record in records if record.projection.address.stable_key() > after.stable_key())


def _require_order(order: int) -> None:
    if type(order) is not int or not 0 <= order <= MAX_SURFACE_ORDER:
        raise ValueError("surface order must be between 0 and 2")


def _require_page(plane: SurfacePlane, order: int, after: GeometryAddress | None, limit: int) -> None:
    _require_order(order)
    if type(limit) is not int or not 1 <= limit <= MAX_PAGE_SIZE:
        raise ValueError("surface page limit is out of bounds")
    if after is not None:
        _require_address_for_order(plane, order, after, "after")


def _require_address_for_order(plane: SurfacePlane, order: int, address: object, name: str) -> None:
    if type(address) is not GeometryAddress:
        raise TypeError(f"{name} must be GeometryAddress")
    if (
        address.profile_id,
        address.chart_id,
        address.phase,
        address.layer,
    ) != (plane.profile_id, plane.chart_id, plane.phase, plane.base_layer - order):
        raise ValueError(f"{name} does not belong to the requested Surface order")


def _hex_distance(left: GeometryAddress, right: GeometryAddress) -> int:
    dq, dr = left.q - right.q, left.r - right.r
    return max(abs(dq), abs(dr), abs(dq + dr))
