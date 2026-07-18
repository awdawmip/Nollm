from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json

from .axial import AxialCoord, hex_distance
from .geometry import GeometryAddress
from .surface import PhysicalFieldScope


MAX_INTERNAL_CANDIDATES = 64
MAX_OUTPUT_CANDIDATES = 8
MAX_RELATION_GROUPS = 4
MAX_CELLS_PER_RELATION_GROUP = 4
MAX_RELATION_GROUP_UNIVERSE = 1024


@dataclass(frozen=True)
class JunctionRequest:
    scope: PhysicalFieldScope
    primary_cells: tuple[GeometryAddress, ...]
    contact_cells: tuple[GeometryAddress, ...] = ()
    max_radius: int = 4
    candidate_limit: int = 8
    active_hex_radius: int = 1 << 30

    def __post_init__(self) -> None:
        if type(self.scope) is not PhysicalFieldScope:
            raise TypeError("scope must be PhysicalFieldScope")
        for name, cells in (("primary_cells", self.primary_cells), ("contact_cells", self.contact_cells)):
            if type(cells) is not tuple or any(type(cell) is not GeometryAddress for cell in cells):
                raise TypeError(f"{name} must be a GeometryAddress tuple")
            if tuple(sorted(set(cells), key=lambda cell: cell.stable_key())) != cells:
                raise ValueError(f"{name} must be a canonical unique tuple")
            if len(cells) > 8 or any(not self.scope.contains(cell) for cell in cells):
                raise ValueError(f"{name} exceeds budget or scope")
        if not self.primary_cells and self.contact_cells:
            raise ValueError("contact_cells require at least one primary cell")
        if type(self.max_radius) is not int or not 1 <= self.max_radius <= 8:
            raise ValueError("max_radius must be in [1,8]")
        if type(self.candidate_limit) is not int or not 1 <= self.candidate_limit <= MAX_OUTPUT_CANDIDATES:
            raise ValueError("candidate_limit must be in [1,8]")
        if type(self.active_hex_radius) is not int or self.active_hex_radius < 1:
            raise ValueError("active_hex_radius must be positive")


@dataclass(frozen=True)
class JunctionCandidate:
    candidate_id: str
    cell: GeometryAddress
    free_face_count: int
    occupied_neighbor_count: int
    primary_max_distance: int
    contact_max_distance: int
    total_distance: int
    boundary: bool

    def to_mapping(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "cell": self.cell.to_mapping(),
            "free_face_count": self.free_face_count,
            "occupied_neighbor_count": self.occupied_neighbor_count,
            "primary_max_distance": self.primary_max_distance,
            "contact_max_distance": self.contact_max_distance,
            "total_distance": self.total_distance,
            "boundary": self.boundary,
        }


@dataclass(frozen=True)
class RelationGroupJunctionRequest:
    scope: PhysicalFieldScope
    relation_groups: tuple[tuple[GeometryAddress, ...], ...]
    max_radius: int = 4
    contact_radius: int = 2
    candidate_limit: int = 8
    active_hex_radius: int = 1 << 30

    def __post_init__(self) -> None:
        if type(self.scope) is not PhysicalFieldScope:
            raise TypeError("scope must be PhysicalFieldScope")
        if type(self.relation_groups) is not tuple or not 1 <= len(self.relation_groups) <= MAX_RELATION_GROUPS:
            raise ValueError("relation_groups must contain one to four groups")
        identities = []
        for group in self.relation_groups:
            if type(group) is not tuple or not 1 <= len(group) <= MAX_CELLS_PER_RELATION_GROUP:
                raise ValueError("each relation group must contain one to four cells")
            if any(type(cell) is not GeometryAddress or not self.scope.contains(cell) for cell in group):
                raise ValueError("relation group cells must belong to the field scope")
            if tuple(sorted(set(group), key=lambda cell: cell.stable_key())) != group:
                raise ValueError("relation group cells must be a canonical unique tuple")
            identities.append(tuple(cell.stable_key() for cell in group))
        if len(identities) != len(set(identities)):
            raise ValueError("relation groups must be unique")
        if type(self.max_radius) is not int or not 1 <= self.max_radius <= 4:
            raise ValueError("max_radius must be in [1,4]")
        if type(self.contact_radius) is not int or not 1 <= self.contact_radius <= self.max_radius:
            raise ValueError("contact_radius must be in [1,max_radius]")
        if type(self.candidate_limit) is not int or not 1 <= self.candidate_limit <= MAX_OUTPUT_CANDIDATES:
            raise ValueError("candidate_limit must be in [1,8]")
        if type(self.active_hex_radius) is not int or self.active_hex_radius < 1:
            raise ValueError("active_hex_radius must be positive")


@dataclass(frozen=True)
class RelationGroupJunctionCandidate:
    candidate_id: str
    cell: GeometryAddress
    group_distances: tuple[int, ...]
    groups_within_contact_radius: int
    all_groups_realized: bool
    max_group_distance: int
    total_group_distance: int
    free_face_count: int
    occupied_neighbor_count: int
    boundary: bool

    def to_mapping(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "cell": self.cell.to_mapping(),
            "group_distances": list(self.group_distances),
            "groups_within_contact_radius": self.groups_within_contact_radius,
            "all_groups_realized": self.all_groups_realized,
            "max_group_distance": self.max_group_distance,
            "total_group_distance": self.total_group_distance,
            "free_face_count": self.free_face_count,
            "occupied_neighbor_count": self.occupied_neighbor_count,
            "boundary": self.boundary,
        }


def solve_junction_candidates(
    request: JunctionRequest,
    occupied_cells: tuple[GeometryAddress, ...],
) -> tuple[JunctionCandidate, ...]:
    if type(request) is not JunctionRequest:
        raise TypeError("request must be JunctionRequest")
    if type(occupied_cells) is not tuple or any(type(cell) is not GeometryAddress for cell in occupied_cells):
        raise TypeError("occupied_cells must be a GeometryAddress tuple")
    occupied = frozenset(cell for cell in occupied_cells if request.scope.contains(cell))
    anchors = request.primary_cells or (
        GeometryAddress(request.scope.profile_id, request.scope.chart_id, request.scope.reference_layer, 0, 0, None),
    )
    universe: set[GeometryAddress] = set()
    for anchor in anchors:
        for q in range(anchor.q - request.max_radius, anchor.q + request.max_radius + 1):
            for r in range(anchor.r - request.max_radius, anchor.r + request.max_radius + 1):
                cell = GeometryAddress(anchor.profile_id, anchor.chart_id, anchor.layer, q, r, anchor.phase)
                if _distance(cell, anchor) > request.max_radius or cell in occupied or not _active(cell, request.active_hex_radius):
                    continue
                universe.add(cell)
    ordered_universe = tuple(sorted(universe, key=lambda cell: cell.stable_key()))[:MAX_INTERNAL_CANDIDATES]
    candidates = tuple(_candidate(request, cell, occupied) for cell in ordered_universe)
    ranked = sorted(candidates, key=lambda item: (
        item.primary_max_distance,
        item.contact_max_distance,
        item.total_distance,
        -item.free_face_count,
        item.occupied_neighbor_count,
        item.cell.stable_key(),
    ))
    return tuple(ranked[: request.candidate_limit])


def solve_relation_group_junction_candidates(
    request: RelationGroupJunctionRequest,
    occupied_cells: tuple[GeometryAddress, ...],
) -> tuple[RelationGroupJunctionCandidate, ...]:
    if type(request) is not RelationGroupJunctionRequest:
        raise TypeError("request must be RelationGroupJunctionRequest")
    if type(occupied_cells) is not tuple or any(type(cell) is not GeometryAddress for cell in occupied_cells):
        raise TypeError("occupied_cells must be a GeometryAddress tuple")
    occupied = frozenset(cell for cell in occupied_cells if request.scope.contains(cell))
    universe: set[GeometryAddress] = set()
    for group in request.relation_groups:
        for anchor in group:
            for q in range(anchor.q - request.max_radius, anchor.q + request.max_radius + 1):
                for r in range(anchor.r - request.max_radius, anchor.r + request.max_radius + 1):
                    cell = GeometryAddress(anchor.profile_id, anchor.chart_id, anchor.layer, q, r, anchor.phase)
                    if _distance(cell, anchor) > request.max_radius or cell in occupied or not _active(cell, request.active_hex_radius):
                        continue
                    universe.add(cell)
    if len(universe) > MAX_RELATION_GROUP_UNIVERSE:
        raise ValueError("relation-group Junction candidate universe exceeds deterministic ceiling")
    candidates = tuple(
        candidate
        for cell in universe
        for candidate in (_relation_group_candidate(request, cell, occupied),)
        if candidate.max_group_distance <= request.max_radius and candidate.all_groups_realized
    )
    ranked = sorted(candidates, key=lambda item: (
        -item.groups_within_contact_radius,
        item.max_group_distance,
        item.total_group_distance,
        not item.boundary,
        -item.free_face_count,
        item.occupied_neighbor_count,
        item.cell.stable_key(),
    ))
    return tuple(ranked[: request.candidate_limit])


def _candidate(request: JunctionRequest, cell: GeometryAddress, occupied: frozenset[GeometryAddress]) -> JunctionCandidate:
    occupied_neighbors = sum(neighbor in occupied for neighbor in cell.lateral(1))
    primary_cells = request.primary_cells or (
        GeometryAddress(request.scope.profile_id, request.scope.chart_id, request.scope.reference_layer, 0, 0, None),
    )
    primary_distances = tuple(_distance(cell, target) for target in primary_cells)
    contact_distances = tuple(_distance(cell, target) for target in request.contact_cells)
    primary_max = max(primary_distances, default=0)
    contact_max = max(contact_distances, default=0)
    total = sum(primary_distances) + sum(contact_distances)
    payload = json.dumps({"scope": request.scope.identity, "cell": cell.to_mapping()}, sort_keys=True, separators=(",", ":")).encode("ascii")
    return JunctionCandidate(
        f"junction:{sha256(payload).hexdigest()}", cell, 6 - occupied_neighbors,
        occupied_neighbors, primary_max, contact_max, total, occupied_neighbors > 0,
    )


def _relation_group_candidate(
    request: RelationGroupJunctionRequest,
    cell: GeometryAddress,
    occupied: frozenset[GeometryAddress],
) -> RelationGroupJunctionCandidate:
    distances = tuple(min(_distance(cell, target) for target in group) for group in request.relation_groups)
    within = sum(distance <= request.contact_radius for distance in distances)
    occupied_neighbors = sum(neighbor in occupied for neighbor in cell.lateral(1))
    payload = json.dumps({"scope": request.scope.identity, "cell": cell.to_mapping()}, sort_keys=True, separators=(",", ":")).encode("ascii")
    return RelationGroupJunctionCandidate(
        f"relation-junction:{sha256(payload).hexdigest()}", cell, distances, within,
        within == len(distances), max(distances), sum(distances), 6 - occupied_neighbors,
        occupied_neighbors, occupied_neighbors > 0,
    )


def _distance(left: GeometryAddress, right: GeometryAddress) -> int:
    if left.profile_id != right.profile_id or left.chart_id != right.chart_id or left.layer != right.layer or left.phase != right.phase:
        raise ValueError("Junction distance requires one physical plane")
    return hex_distance(AxialCoord(left.q, left.r), AxialCoord(right.q, right.r))


def _active(cell: GeometryAddress, radius: int) -> bool:
    return max(abs(cell.q), abs(cell.r), abs(cell.q + cell.r)) <= radius
