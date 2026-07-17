from __future__ import annotations

from dataclasses import dataclass

from nollm_core import GeometryAddress, PhysicalFieldScope


LOCALITY_ATLAS_SCHEMA_VERSION = "nollm_access_locality_atlas_v1"


@dataclass(frozen=True)
class LocalityCandidateRef:
    candidate_id: str
    geometry_address: GeometryAddress
    occupied: bool
    boundary: bool
    free_face_count: int
    occupied_neighbor_count: int
    representative_statements: tuple[dict[str, object], ...] = ()

    def __post_init__(self) -> None:
        if type(self.candidate_id) is not str or not self.candidate_id or type(self.geometry_address) is not GeometryAddress:
            raise TypeError("candidate identity and GeometryAddress are required")
        if type(self.occupied) is not bool or type(self.boundary) is not bool:
            raise TypeError("Locality state flags must be bool")
        if type(self.free_face_count) is not int or not 0 <= self.free_face_count <= 6:
            raise ValueError("free_face_count must be in [0,6]")
        if type(self.occupied_neighbor_count) is not int or not 0 <= self.occupied_neighbor_count <= 6:
            raise ValueError("occupied_neighbor_count must be in [0,6]")
        if type(self.representative_statements) is not tuple or len(self.representative_statements) > 3:
            raise TypeError("representative_statements must be a bounded tuple")

    def to_mapping(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "geometry_address": self.geometry_address.to_mapping(),
            "occupied": self.occupied,
            "boundary": self.boundary,
            "free_face_count": self.free_face_count,
            "occupied_neighbor_count": self.occupied_neighbor_count,
            "representative_statements": list(self.representative_statements),
        }

    @classmethod
    def from_mapping(cls, value: object) -> "LocalityCandidateRef":
        keys = {"candidate_id", "geometry_address", "occupied", "boundary", "free_face_count", "occupied_neighbor_count", "representative_statements"}
        if type(value) is not dict or set(value) != keys or type(value["representative_statements"]) is not list:
            raise ValueError("invalid LocalityCandidateRef mapping")
        return cls(
            value["candidate_id"], GeometryAddress.from_mapping(value["geometry_address"]),
            value["occupied"], value["boundary"], value["free_face_count"],
            value["occupied_neighbor_count"], tuple(value["representative_statements"]),
        )


@dataclass(frozen=True)
class LocalityAtlas:
    request_id: str
    scope: PhysicalFieldScope
    core_state_sha256: str
    atlas_fingerprint: str
    candidates: tuple[LocalityCandidateRef, ...]
    schema_version: str = LOCALITY_ATLAS_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if type(self.request_id) is not str or not self.request_id:
            raise TypeError("request_id is required")
        if type(self.scope) is not PhysicalFieldScope:
            raise TypeError("scope must be PhysicalFieldScope")
        if any(type(value) is not str or len(value) != 64 for value in (self.core_state_sha256, self.atlas_fingerprint)):
            raise ValueError("Atlas hashes must be SHA-256 hex strings")
        if type(self.candidates) is not tuple or not self.candidates or len(self.candidates) > 64:
            raise ValueError("Atlas candidates must be finite and non-empty")
        ids = tuple(item.candidate_id for item in self.candidates)
        if len(ids) != len(set(ids)) or self.schema_version != LOCALITY_ATLAS_SCHEMA_VERSION:
            raise ValueError("Atlas candidates or schema are invalid")

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "request_id": self.request_id,
            "field_scope": self.scope.to_mapping(),
            "core_state_sha256": self.core_state_sha256,
            "atlas_fingerprint": self.atlas_fingerprint,
            "candidates": [item.to_mapping() for item in self.candidates],
        }

    @classmethod
    def from_mapping(cls, value: object) -> "LocalityAtlas":
        keys = {"schema_version", "request_id", "field_scope", "core_state_sha256", "atlas_fingerprint", "candidates"}
        if type(value) is not dict or set(value) != keys or type(value["candidates"]) is not list:
            raise ValueError("invalid LocalityAtlas mapping")
        return cls(
            value["request_id"], PhysicalFieldScope.from_mapping(value["field_scope"]),
            value["core_state_sha256"], value["atlas_fingerprint"],
            tuple(LocalityCandidateRef.from_mapping(item) for item in value["candidates"]), value["schema_version"],
        )
