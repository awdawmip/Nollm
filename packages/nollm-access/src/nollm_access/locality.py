from __future__ import annotations

from dataclasses import dataclass

from nollm_core import GeometryAddress, PhysicalFieldScope


LOCALITY_ATLAS_SCHEMA_VERSION = "nollm_access_locality_atlas_v2"
LEGACY_LOCALITY_ATLAS_SCHEMA_VERSION = "nollm_access_locality_atlas_v1"


@dataclass(frozen=True)
class LocalityCandidateRef:
    candidate_id: str
    geometry_addresses: tuple[GeometryAddress, ...]
    occupied: bool
    boundary: bool
    free_face_count: int
    occupied_neighbor_count: int
    representative_statements: tuple[dict[str, object], ...] = ()

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
        }

    @classmethod
    def from_mapping(cls, value: object) -> "LocalityCandidateRef":
        current = {"candidate_id", "geometry_addresses", "occupied", "boundary", "free_face_count", "occupied_neighbor_count", "representative_statements"}
        legacy = {"candidate_id", "geometry_address", "occupied", "boundary", "free_face_count", "occupied_neighbor_count", "representative_statements"}
        if type(value) is not dict or frozenset(value) not in {frozenset(current), frozenset(legacy)} or type(value["representative_statements"]) is not list:
            raise ValueError("invalid LocalityCandidateRef mapping")
        raw_addresses = value.get("geometry_addresses")
        if raw_addresses is None:
            raw_addresses = [value["geometry_address"]]
        if type(raw_addresses) is not list:
            raise ValueError("invalid Locality geometry mapping")
        return cls(
            value["candidate_id"], tuple(GeometryAddress.from_mapping(item) for item in raw_addresses),
            value["occupied"], value["boundary"], value["free_face_count"],
            value["occupied_neighbor_count"], tuple(value["representative_statements"]),
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
        }

    @classmethod
    def from_mapping(cls, value: object) -> "AtlasNode":
        keys = {"node_id", "aggregation_order", "geometry_identity", "child_node_ids", "occupied_cell_count", "native_atom_count", "truncated", "representative_statements"}
        if type(value) is not dict or set(value) != keys or type(value["child_node_ids"]) is not list or type(value["representative_statements"]) is not list:
            raise ValueError("invalid AtlasNode mapping")
        return cls(value["node_id"], value["aggregation_order"], value["geometry_identity"], tuple(value["child_node_ids"]), value["occupied_cell_count"], value["native_atom_count"], value["truncated"], tuple(value["representative_statements"]))


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
        if type(self.leaf_locality_candidate_ids) is not tuple or not 1 <= len(self.leaf_locality_candidate_ids) <= 4:
            raise ValueError("Atlas path must expose one to four leaf Localities")

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
    schema_version: str = LOCALITY_ATLAS_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if type(self.request_id) is not str or not self.request_id or type(self.scope) is not PhysicalFieldScope:
            raise TypeError("Atlas request and scope are required")
        if any(type(value) is not str or len(value) != 64 for value in (self.core_state_sha256, self.atlas_fingerprint)):
            raise ValueError("Atlas hashes must be SHA-256 hex strings")
        if type(self.candidates) is not tuple or not self.candidates or len(self.candidates) > 32:
            raise ValueError("Atlas candidates must be finite and non-empty")
        if type(self.nodes) is not tuple or len(self.nodes) > 64 or type(self.paths) is not tuple or len(self.paths) > 32:
            raise ValueError("Atlas hierarchy exceeds its fixed budget")
        candidate_ids = tuple(item.candidate_id for item in self.candidates)
        node_ids = tuple(item.node_id for item in self.nodes)
        path_ids = tuple(item.path_id for item in self.paths)
        if len(candidate_ids) != len(set(candidate_ids)) or len(node_ids) != len(set(node_ids)) or len(path_ids) != len(set(path_ids)):
            raise ValueError("Atlas identities must be unique")
        if self.schema_version != LOCALITY_ATLAS_SCHEMA_VERSION:
            raise ValueError("Atlas schema is not active")
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
            return cls(value["request_id"], PhysicalFieldScope.from_mapping(value["field_scope"]), value["core_state_sha256"], value["atlas_fingerprint"], candidates, nodes, paths)
        keys = {"schema_version", "request_id", "field_scope", "core_state_sha256", "atlas_fingerprint", "nodes", "paths", "candidates"}
        if schema != LOCALITY_ATLAS_SCHEMA_VERSION or set(value) != keys or any(type(value[name]) is not list for name in ("nodes", "paths", "candidates")):
            raise ValueError("invalid LocalityAtlas mapping")
        return cls(
            value["request_id"], PhysicalFieldScope.from_mapping(value["field_scope"]), value["core_state_sha256"], value["atlas_fingerprint"],
            tuple(LocalityCandidateRef.from_mapping(item) for item in value["candidates"]),
            tuple(AtlasNode.from_mapping(item) for item in value["nodes"]),
            tuple(AtlasPath.from_mapping(item) for item in value["paths"]), value["schema_version"],
        )
