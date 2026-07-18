from __future__ import annotations

from dataclasses import dataclass

from nollm_core import GeometryAddress, PhysicalFieldScope


LOCALITY_ATLAS_SCHEMA_VERSION = "nollm_access_locality_atlas_v3"
REV1_LOCALITY_ATLAS_SCHEMA_VERSION = "nollm_access_locality_atlas_v2"
LEGACY_LOCALITY_ATLAS_SCHEMA_VERSION = "nollm_access_locality_atlas_v1"
MAX_ATLAS_REGIONS = 512
MAX_ATLAS_NODES = 512
MAX_ATLAS_PATHS = 512


@dataclass(frozen=True)
class LocalityCandidateRef:
    candidate_id: str
    geometry_addresses: tuple[GeometryAddress, ...]
    occupied: bool
    boundary: bool
    free_face_count: int
    occupied_neighbor_count: int
    representative_statements: tuple[dict[str, object], ...] = ()
    source_cell_count: int = 0
    support_method: str = "geometry_center_farthest_v1"
    support_overflow: bool = False

    def __post_init__(self) -> None:
        if type(self.candidate_id) is not str or not self.candidate_id:
            raise TypeError("candidate identity is required")
        if type(self.geometry_addresses) is not tuple or not 1 <= len(self.geometry_addresses) <= 4:
            raise ValueError("Locality geometry must contain one to four cells")
        if any(type(item) is not GeometryAddress for item in self.geometry_addresses):
            raise TypeError("Locality geometry must contain GeometryAddress values")
        if tuple(sorted(set(self.geometry_addresses), key=lambda item: item.stable_key())) != self.geometry_addresses:
            raise ValueError("Locality geometry must be canonical and unique")
        if type(self.occupied) is not bool or type(self.boundary) is not bool:
            raise TypeError("Locality state flags must be bool")
        if type(self.free_face_count) is not int or not 0 <= self.free_face_count <= 6:
            raise ValueError("free_face_count must be in [0,6]")
        if type(self.occupied_neighbor_count) is not int or not 0 <= self.occupied_neighbor_count <= 6:
            raise ValueError("occupied_neighbor_count must be in [0,6]")
        if type(self.representative_statements) is not tuple or len(self.representative_statements) > 3:
            raise TypeError("representative_statements must be a bounded tuple")
        minimum_sources = len(self.geometry_addresses) if self.occupied else 0
        if type(self.source_cell_count) is not int or self.source_cell_count < minimum_sources:
            raise ValueError("source_cell_count must cover the geometry support")
        if type(self.support_method) is not str or not self.support_method or type(self.support_overflow) is not bool:
            raise ValueError("Locality support contract is invalid")

    @property
    def geometry_address(self) -> GeometryAddress:
        return self.geometry_addresses[0]

    def to_mapping(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "geometry_addresses": [item.to_mapping() for item in self.geometry_addresses],
            "occupied": self.occupied,
            "boundary": self.boundary,
            "free_face_count": self.free_face_count,
            "occupied_neighbor_count": self.occupied_neighbor_count,
            "representative_statements": list(self.representative_statements),
            "source_cell_count": self.source_cell_count,
            "support_cell_count": len(self.geometry_addresses),
            "support_method": self.support_method,
            "support_overflow": self.support_overflow,
        }

    @classmethod
    def from_mapping(cls, value: object) -> "LocalityCandidateRef":
        current = {"candidate_id", "geometry_addresses", "occupied", "boundary", "free_face_count", "occupied_neighbor_count", "representative_statements", "source_cell_count", "support_cell_count", "support_method", "support_overflow"}
        rev1 = {"candidate_id", "geometry_addresses", "occupied", "boundary", "free_face_count", "occupied_neighbor_count", "representative_statements"}
        legacy = {"candidate_id", "geometry_address", "occupied", "boundary", "free_face_count", "occupied_neighbor_count", "representative_statements"}
        if type(value) is not dict or frozenset(value) not in {frozenset(current), frozenset(rev1), frozenset(legacy)} or type(value["representative_statements"]) is not list:
            raise ValueError("invalid LocalityCandidateRef mapping")
        raw_addresses = value.get("geometry_addresses")
        if raw_addresses is None:
            raw_addresses = [value["geometry_address"]]
        if type(raw_addresses) is not list:
            raise ValueError("invalid Locality geometry mapping")
        if "support_cell_count" in value and value["support_cell_count"] != len(raw_addresses):
            raise ValueError("Locality support cell count is not canonical")
        return cls(
            value["candidate_id"], tuple(GeometryAddress.from_mapping(item) for item in raw_addresses),
            value["occupied"], value["boundary"], value["free_face_count"],
            value["occupied_neighbor_count"], tuple(value["representative_statements"]),
            value.get("source_cell_count", len(raw_addresses)), value.get("support_method", "legacy_geometry_support"),
            value.get("support_overflow", False),
        )


@dataclass(frozen=True)
class AtlasNode:
    node_id: str
    aggregation_order: int
    geometry_identity: dict[str, object]
    child_node_ids: tuple[str, ...]
    occupied_cell_count: int
    native_atom_count: int
    truncated: bool
    representative_statements: tuple[dict[str, object], ...] = ()
    source_cell_count: int = 0
    support_cell_count: int = 0
    support_method: str = "geometry_center_farthest_v1"
    support_overflow: bool = False

    def __post_init__(self) -> None:
        if type(self.node_id) is not str or not self.node_id or type(self.aggregation_order) is not int or self.aggregation_order < 0:
            raise ValueError("Atlas node identity and order are invalid")
        if type(self.geometry_identity) is not dict or type(self.child_node_ids) is not tuple:
            raise TypeError("Atlas node geometry and children are invalid")
        if tuple(sorted(set(self.child_node_ids))) != self.child_node_ids:
            raise ValueError("Atlas child IDs must be canonical and unique")
        if any(type(value) is not int or value < 0 for value in (self.occupied_cell_count, self.native_atom_count)):
            raise ValueError("Atlas node counts must be non-negative")
        if type(self.truncated) is not bool or type(self.representative_statements) is not tuple or len(self.representative_statements) > 3:
            raise ValueError("Atlas node bounded fields are invalid")
        if type(self.source_cell_count) is not int or self.source_cell_count < 0 or type(self.support_cell_count) is not int or not 0 <= self.support_cell_count <= 4:
            raise ValueError("Atlas node support counts are invalid")
        if type(self.support_method) is not str or not self.support_method or type(self.support_overflow) is not bool:
            raise ValueError("Atlas node support contract is invalid")

    def to_mapping(self) -> dict[str, object]:
        return {
            "node_id": self.node_id,
            "aggregation_order": self.aggregation_order,
            "geometry_identity": self.geometry_identity,
            "child_node_ids": list(self.child_node_ids),
            "occupied_cell_count": self.occupied_cell_count,
            "native_atom_count": self.native_atom_count,
            "truncated": self.truncated,
            "representative_statements": list(self.representative_statements),
            "source_cell_count": self.source_cell_count,
            "support_cell_count": self.support_cell_count,
            "support_method": self.support_method,
            "support_overflow": self.support_overflow,
        }

    @classmethod
    def from_mapping(cls, value: object) -> "AtlasNode":
        keys = {"node_id", "aggregation_order", "geometry_identity", "child_node_ids", "occupied_cell_count", "native_atom_count", "truncated", "representative_statements", "source_cell_count", "support_cell_count", "support_method", "support_overflow"}
        rev1 = {"node_id", "aggregation_order", "geometry_identity", "child_node_ids", "occupied_cell_count", "native_atom_count", "truncated", "representative_statements"}
        if type(value) is not dict or (set(value) != keys and set(value) != rev1) or type(value["child_node_ids"]) is not list or type(value["representative_statements"]) is not list:
            raise ValueError("invalid AtlasNode mapping")
        return cls(
            value["node_id"], value["aggregation_order"], value["geometry_identity"], tuple(value["child_node_ids"]),
            value["occupied_cell_count"], value["native_atom_count"], value["truncated"], tuple(value["representative_statements"]),
            value.get("source_cell_count", value["occupied_cell_count"]), value.get("support_cell_count", 0),
            value.get("support_method", "legacy_geometry_support"), value.get("support_overflow", False),
        )


@dataclass(frozen=True)
class AtlasPath:
    path_id: str
    node_ids: tuple[str, ...]
    leaf_locality_candidate_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self.path_id) is not str or not self.path_id:
            raise TypeError("Atlas path identity is required")
        if type(self.node_ids) is not tuple or not self.node_ids or len(self.node_ids) > 3:
            raise ValueError("Atlas path must contain one to three nodes")
        if type(self.leaf_locality_candidate_ids) is not tuple or len(self.leaf_locality_candidate_ids) > 4:
            raise ValueError("Atlas path must expose zero to four leaf Localities")

    def to_mapping(self) -> dict[str, object]:
        return {"path_id": self.path_id, "node_ids": list(self.node_ids), "leaf_locality_candidate_ids": list(self.leaf_locality_candidate_ids)}

    @classmethod
    def from_mapping(cls, value: object) -> "AtlasPath":
        if type(value) is not dict or set(value) != {"path_id", "node_ids", "leaf_locality_candidate_ids"} or type(value["node_ids"]) is not list or type(value["leaf_locality_candidate_ids"]) is not list:
            raise ValueError("invalid AtlasPath mapping")
        return cls(value["path_id"], tuple(value["node_ids"]), tuple(value["leaf_locality_candidate_ids"]))


@dataclass(frozen=True)
class LocalityAtlas:
    request_id: str
    scope: PhysicalFieldScope
    core_state_sha256: str
    atlas_fingerprint: str
    candidates: tuple[LocalityCandidateRef, ...]
    nodes: tuple[AtlasNode, ...] = ()
    paths: tuple[AtlasPath, ...] = ()
    occupied_field_cell_count: int = 0
    covered_field_cell_count: int = 0
    uncovered_field_cell_count: int = 0
    selected_aggregation_order: int | None = 0
    region_count: int = 0
    overflow: bool = False
    order_projection_counts: tuple[int, ...] = ()
    schema_version: str = LOCALITY_ATLAS_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if type(self.request_id) is not str or not self.request_id or type(self.scope) is not PhysicalFieldScope:
            raise TypeError("Atlas request and scope are required")
        if any(type(value) is not str or len(value) != 64 for value in (self.core_state_sha256, self.atlas_fingerprint)):
            raise ValueError("Atlas hashes must be SHA-256 hex strings")
        if type(self.candidates) is not tuple or len(self.candidates) > MAX_ATLAS_REGIONS or (not self.candidates and not self.overflow):
            raise ValueError("Atlas candidates must be finite and active or explicitly overflowed")
        if type(self.nodes) is not tuple or len(self.nodes) > MAX_ATLAS_NODES or type(self.paths) is not tuple or len(self.paths) > MAX_ATLAS_PATHS:
            raise ValueError("Atlas hierarchy exceeds its fixed budget")
        candidate_ids = tuple(item.candidate_id for item in self.candidates)
        node_ids = tuple(item.node_id for item in self.nodes)
        path_ids = tuple(item.path_id for item in self.paths)
        if len(candidate_ids) != len(set(candidate_ids)) or len(node_ids) != len(set(node_ids)) or len(path_ids) != len(set(path_ids)):
            raise ValueError("Atlas identities must be unique")
        if self.schema_version != LOCALITY_ATLAS_SCHEMA_VERSION:
            raise ValueError("Atlas schema is not active")
        counts = (self.occupied_field_cell_count, self.covered_field_cell_count, self.uncovered_field_cell_count, self.region_count)
        if any(type(value) is not int or value < 0 for value in counts):
            raise ValueError("Atlas coverage certificate counts are invalid")
        if self.covered_field_cell_count + self.uncovered_field_cell_count != self.occupied_field_cell_count:
            raise ValueError("Atlas coverage certificate does not balance")
        if type(self.overflow) is not bool or type(self.order_projection_counts) is not tuple or any(type(value) is not int or value < 0 for value in self.order_projection_counts):
            raise ValueError("Atlas order certificate is invalid")
        if self.selected_aggregation_order is not None and (type(self.selected_aggregation_order) is not int or not 0 <= self.selected_aggregation_order <= 8):
            raise ValueError("Atlas selected aggregation order is invalid")
        if self.overflow:
            if self.selected_aggregation_order is not None or self.candidates or self.nodes or self.paths or self.covered_field_cell_count != 0 or self.uncovered_field_cell_count != self.occupied_field_cell_count:
                raise ValueError("overflow Atlas must not expose sampled Localities")
        elif self.uncovered_field_cell_count != 0 or self.covered_field_cell_count != self.occupied_field_cell_count:
            raise ValueError("active Atlas must cover every occupied field Cell")
        if self.region_count != (0 if self.overflow else sum(node.aggregation_order == self.selected_aggregation_order for node in self.nodes)):
            raise ValueError("Atlas region count does not match its selected-order nodes")
        node_set, candidate_set = set(node_ids), set(candidate_ids)
        if any(any(node not in node_set for node in path.node_ids) or any(leaf not in candidate_set for leaf in path.leaf_locality_candidate_ids) for path in self.paths):
            raise ValueError("Atlas paths must bind current nodes and leaf Localities")

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "request_id": self.request_id,
            "field_scope": self.scope.to_mapping(),
            "core_state_sha256": self.core_state_sha256,
            "atlas_fingerprint": self.atlas_fingerprint,
            "nodes": [item.to_mapping() for item in self.nodes],
            "paths": [item.to_mapping() for item in self.paths],
            "candidates": [item.to_mapping() for item in self.candidates],
            "coverage_certificate": {
                "occupied_field_cell_count": self.occupied_field_cell_count,
                "covered_field_cell_count": self.covered_field_cell_count,
                "uncovered_field_cell_count": self.uncovered_field_cell_count,
                "selected_aggregation_order": self.selected_aggregation_order,
                "region_count": self.region_count,
                "overflow": self.overflow,
                "order_projection_counts": list(self.order_projection_counts),
            },
        }

    @classmethod
    def from_mapping(cls, value: object) -> "LocalityAtlas":
        if type(value) is not dict:
            raise ValueError("invalid LocalityAtlas mapping")
        schema = value.get("schema_version")
        if schema == LEGACY_LOCALITY_ATLAS_SCHEMA_VERSION:
            keys = {"schema_version", "request_id", "field_scope", "core_state_sha256", "atlas_fingerprint", "candidates"}
            if set(value) != keys or type(value["candidates"]) is not list:
                raise ValueError("invalid legacy LocalityAtlas mapping")
            candidates = tuple(LocalityCandidateRef.from_mapping(item) for item in value["candidates"])
            nodes = tuple(AtlasNode(f"legacy-node:{index}", 0, item.geometry_address.to_mapping(), (), 1 if item.occupied else 0, len(item.representative_statements), False, item.representative_statements) for index, item in enumerate(candidates))
            paths = tuple(AtlasPath(f"legacy-path:{index}", (nodes[index].node_id,), (item.candidate_id,)) for index, item in enumerate(candidates))
            occupied_count = sum(item.occupied for item in candidates)
            return cls(value["request_id"], PhysicalFieldScope.from_mapping(value["field_scope"]), value["core_state_sha256"], value["atlas_fingerprint"], candidates, nodes, paths, occupied_count, occupied_count, 0, 0, len(nodes), False, (len(nodes),))
        rev1_keys = {"schema_version", "request_id", "field_scope", "core_state_sha256", "atlas_fingerprint", "nodes", "paths", "candidates"}
        if schema == REV1_LOCALITY_ATLAS_SCHEMA_VERSION and set(value) == rev1_keys and all(type(value[name]) is list for name in ("nodes", "paths", "candidates")):
            candidates = tuple(LocalityCandidateRef.from_mapping(item) for item in value["candidates"])
            nodes = tuple(AtlasNode.from_mapping(item) for item in value["nodes"])
            paths = tuple(AtlasPath.from_mapping(item) for item in value["paths"])
            occupied_count = sum(item.source_cell_count for item in candidates if item.occupied)
            return cls(value["request_id"], PhysicalFieldScope.from_mapping(value["field_scope"]), value["core_state_sha256"], value["atlas_fingerprint"], candidates, nodes, paths, occupied_count, occupied_count, 0, nodes[0].aggregation_order if nodes else 0, len(nodes), False, (len(nodes),))
        keys = rev1_keys | {"coverage_certificate"}
        if schema != LOCALITY_ATLAS_SCHEMA_VERSION or set(value) != keys or any(type(value[name]) is not list for name in ("nodes", "paths", "candidates")) or type(value["coverage_certificate"]) is not dict:
            raise ValueError("invalid LocalityAtlas mapping")
        certificate = value["coverage_certificate"]
        certificate_keys = {"occupied_field_cell_count", "covered_field_cell_count", "uncovered_field_cell_count", "selected_aggregation_order", "region_count", "overflow", "order_projection_counts"}
        if set(certificate) != certificate_keys or type(certificate["order_projection_counts"]) is not list:
            raise ValueError("invalid Atlas coverage certificate")
        return cls(
            value["request_id"], PhysicalFieldScope.from_mapping(value["field_scope"]), value["core_state_sha256"], value["atlas_fingerprint"],
            tuple(LocalityCandidateRef.from_mapping(item) for item in value["candidates"]),
            tuple(AtlasNode.from_mapping(item) for item in value["nodes"]), tuple(AtlasPath.from_mapping(item) for item in value["paths"]),
            certificate["occupied_field_cell_count"], certificate["covered_field_cell_count"], certificate["uncovered_field_cell_count"],
            certificate["selected_aggregation_order"], certificate["region_count"], certificate["overflow"],
            tuple(certificate["order_projection_counts"]), value["schema_version"],
        )
