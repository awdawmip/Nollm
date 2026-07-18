from __future__ import annotations

from dataclasses import dataclass

from nollm_core import PhysicalFieldScope


PROGRESSIVE_ATLAS_SCHEMA_VERSION = "nollm_access_progressive_atlas_page_v1"
LOCAL_DETAIL_SCHEMA_VERSION = "nollm_access_local_detail_page_v1"
DEFAULT_MAX_REGIONS_PER_PAGE = 32
DEFAULT_MAX_PROMPT_BYTES = 65536
DEFAULT_MAX_CARTOGRAPHY_DEPTH = 4


@dataclass(frozen=True)
class ProgressiveAtlasPolicy:
    max_regions_per_page: int = DEFAULT_MAX_REGIONS_PER_PAGE
    max_prompt_bytes: int = DEFAULT_MAX_PROMPT_BYTES
    max_depth: int = DEFAULT_MAX_CARTOGRAPHY_DEPTH
    max_order: int = 8
    support_limit: int = 4

    def __post_init__(self) -> None:
        if type(self.max_regions_per_page) is not int or not 1 <= self.max_regions_per_page <= 32:
            raise ValueError("max_regions_per_page must be in [1,32]")
        if type(self.max_prompt_bytes) is not int or not 1024 <= self.max_prompt_bytes <= 65536:
            raise ValueError("max_prompt_bytes must be in [1024,65536]")
        if type(self.max_depth) is not int or not 1 <= self.max_depth <= 8:
            raise ValueError("max_depth must be in [1,8]")
        if type(self.max_order) is not int or not 0 <= self.max_order <= 8:
            raise ValueError("max_order must be in [0,8]")
        if type(self.support_limit) is not int or not 1 <= self.support_limit <= 4:
            raise ValueError("support_limit must be in [1,4]")

    def to_mapping(self) -> dict[str, int]:
        return {
            "max_regions_per_page": self.max_regions_per_page,
            "max_prompt_bytes": self.max_prompt_bytes,
            "max_depth": self.max_depth,
            "max_order": self.max_order,
            "support_limit": self.support_limit,
        }

    @classmethod
    def from_mapping(cls, value: object) -> "ProgressiveAtlasPolicy":
        keys = {"max_regions_per_page", "max_prompt_bytes", "max_depth", "max_order", "support_limit"}
        if type(value) is not dict or set(value) != keys:
            raise ValueError("invalid Progressive Atlas policy")
        return cls(**value)


@dataclass(frozen=True)
class ProgressiveAtlasRegion:
    region_id: str
    geometry_identity: dict[str, object]
    aggregation_order: int
    source_cell_count: int
    native_atom_count: int
    child_region_count: int
    support_entries: tuple[dict[str, object], ...]
    representative_statements: tuple[dict[str, object], ...]
    truncated: bool
    support_overflow: bool

    def __post_init__(self) -> None:
        if type(self.region_id) is not str or not self.region_id:
            raise TypeError("region_id is required")
        if type(self.geometry_identity) is not dict or type(self.aggregation_order) is not int or not 0 <= self.aggregation_order <= 8:
            raise TypeError("region geometry identity and order are invalid")
        if any(type(value) is not int or value < 0 for value in (self.source_cell_count, self.native_atom_count, self.child_region_count)):
            raise ValueError("region counts must be non-negative")
        if type(self.support_entries) is not tuple or not 1 <= len(self.support_entries) <= 4:
            raise ValueError("region support must contain one to four entries")
        if type(self.representative_statements) is not tuple or len(self.representative_statements) > 3:
            raise ValueError("region representatives must be bounded")
        if type(self.truncated) is not bool or type(self.support_overflow) is not bool:
            raise TypeError("region flags must be bool")

    @property
    def leaf(self) -> bool:
        return self.geometry_identity.get("kind") == "physical_cell_v1"

    def to_mapping(self) -> dict[str, object]:
        return {
            "region_id": self.region_id,
            "geometry_identity": self.geometry_identity,
            "aggregation_order": self.aggregation_order,
            "source_cell_count": self.source_cell_count,
            "native_atom_count": self.native_atom_count,
            "child_region_count": self.child_region_count,
            "support_entries": list(self.support_entries),
            "representative_statements": list(self.representative_statements),
            "truncated": self.truncated,
            "support_overflow": self.support_overflow,
            "leaf": self.leaf,
            "local_detail_available": self.native_atom_count > len(self.representative_statements),
        }

    @classmethod
    def from_mapping(cls, value: object) -> "ProgressiveAtlasRegion":
        keys = {
            "region_id", "geometry_identity", "aggregation_order", "source_cell_count",
            "native_atom_count", "child_region_count", "support_entries",
            "representative_statements", "truncated", "support_overflow", "leaf",
            "local_detail_available",
        }
        if type(value) is not dict or set(value) != keys:
            raise ValueError("invalid Progressive Atlas region mapping")
        if type(value["support_entries"]) is not list or type(value["representative_statements"]) is not list:
            raise ValueError("invalid Progressive Atlas region arrays")
        result = cls(
            value["region_id"], value["geometry_identity"], value["aggregation_order"],
            value["source_cell_count"], value["native_atom_count"], value["child_region_count"],
            tuple(value["support_entries"]), tuple(value["representative_statements"]),
            value["truncated"], value["support_overflow"],
        )
        if value["leaf"] != result.leaf or value["local_detail_available"] != (result.native_atom_count > len(result.representative_statements)):
            raise ValueError("Progressive Atlas region derived fields are not canonical")
        return result


@dataclass(frozen=True)
class ProgressiveAtlasPage:
    request_id: str
    scope: PhysicalFieldScope
    core_state_sha256: str
    atlas_fingerprint: str
    page_fingerprint: str
    parent_region_id: str | None
    depth: int
    aggregation_order: int | None
    regions: tuple[ProgressiveAtlasRegion, ...]
    occupied_field_cell_count: int
    covered_source_cell_count: int
    uncovered_source_cell_count: int
    serialized_utf8_bytes: int
    estimated_token_units: int
    overflow: bool
    policy: ProgressiveAtlasPolicy

    def __post_init__(self) -> None:
        if type(self.request_id) is not str or not self.request_id or type(self.scope) is not PhysicalFieldScope:
            raise TypeError("page request and scope are required")
        if any(type(value) is not str or len(value) != 64 for value in (self.core_state_sha256, self.atlas_fingerprint, self.page_fingerprint)):
            raise ValueError("page fingerprints must be SHA-256 text")
        if self.parent_region_id is not None and (type(self.parent_region_id) is not str or not self.parent_region_id):
            raise TypeError("parent_region_id must be null or text")
        if type(self.depth) is not int or not 0 <= self.depth <= self.policy.max_depth:
            raise ValueError("page depth is outside policy")
        if self.aggregation_order is not None and (type(self.aggregation_order) is not int or not 0 <= self.aggregation_order <= self.policy.max_order):
            raise ValueError("page aggregation order is invalid")
        if type(self.regions) is not tuple or len(self.regions) > self.policy.max_regions_per_page:
            raise ValueError("page region count exceeds policy")
        if len({region.region_id for region in self.regions}) != len(self.regions):
            raise ValueError("page region identities must be unique")
        counts = (self.occupied_field_cell_count, self.covered_source_cell_count, self.uncovered_source_cell_count, self.serialized_utf8_bytes, self.estimated_token_units)
        if any(type(value) is not int or value < 0 for value in counts):
            raise ValueError("page certificate counts are invalid")
        if type(self.overflow) is not bool:
            raise TypeError("overflow must be bool")
        if self.overflow:
            if self.regions or self.covered_source_cell_count != 0:
                raise ValueError("overflow page must not expose sampled regions")
        elif not self.regions or self.uncovered_source_cell_count != 0:
            raise ValueError("active page must be complete")
        if self.serialized_utf8_bytes > self.policy.max_prompt_bytes:
            raise ValueError("page exceeds its prompt byte budget")

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema_version": PROGRESSIVE_ATLAS_SCHEMA_VERSION,
            "request_id": self.request_id,
            "field_scope": self.scope.to_mapping(),
            "core_state_sha256": self.core_state_sha256,
            "atlas_fingerprint": self.atlas_fingerprint,
            "page_fingerprint": self.page_fingerprint,
            "parent_region_id": self.parent_region_id,
            "depth": self.depth,
            "aggregation_order": self.aggregation_order,
            "regions": [region.to_mapping() for region in self.regions],
            "coverage_certificate": {
                "occupied_field_cell_count": self.occupied_field_cell_count,
                "covered_source_cell_count": self.covered_source_cell_count,
                "uncovered_source_cell_count": self.uncovered_source_cell_count,
                "region_count": len(self.regions),
                "serialized_utf8_bytes": self.serialized_utf8_bytes,
                "estimated_token_units": self.estimated_token_units,
                "overflow": self.overflow,
            },
            "policy": self.policy.to_mapping(),
        }

    @classmethod
    def from_mapping(cls, value: object) -> "ProgressiveAtlasPage":
        keys = {
            "schema_version", "request_id", "field_scope", "core_state_sha256",
            "atlas_fingerprint", "page_fingerprint", "parent_region_id", "depth",
            "aggregation_order", "regions", "coverage_certificate", "policy",
        }
        if type(value) is not dict or set(value) != keys or value.get("schema_version") != PROGRESSIVE_ATLAS_SCHEMA_VERSION:
            raise ValueError("invalid Progressive Atlas page mapping")
        certificate = value["coverage_certificate"]
        certificate_keys = {
            "occupied_field_cell_count", "covered_source_cell_count", "uncovered_source_cell_count",
            "region_count", "serialized_utf8_bytes", "estimated_token_units", "overflow",
        }
        if type(value["regions"]) is not list or type(certificate) is not dict or set(certificate) != certificate_keys:
            raise ValueError("invalid Progressive Atlas page certificate")
        regions = tuple(ProgressiveAtlasRegion.from_mapping(item) for item in value["regions"])
        if certificate["region_count"] != len(regions):
            raise ValueError("Progressive Atlas region count is not canonical")
        return cls(
            value["request_id"], PhysicalFieldScope.from_mapping(value["field_scope"]),
            value["core_state_sha256"], value["atlas_fingerprint"], value["page_fingerprint"],
            value["parent_region_id"], value["depth"], value["aggregation_order"], regions,
            certificate["occupied_field_cell_count"], certificate["covered_source_cell_count"],
            certificate["uncovered_source_cell_count"], certificate["serialized_utf8_bytes"],
            certificate["estimated_token_units"], certificate["overflow"],
            ProgressiveAtlasPolicy.from_mapping(value["policy"]),
        )


@dataclass(frozen=True)
class LocalDetailPage:
    request_id: str
    core_state_sha256: str
    atlas_fingerprint: str
    region_id: str
    statements: tuple[dict[str, object], ...]
    total_statement_count: int
    has_more: bool

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema_version": LOCAL_DETAIL_SCHEMA_VERSION,
            "request_id": self.request_id,
            "core_state_sha256": self.core_state_sha256,
            "atlas_fingerprint": self.atlas_fingerprint,
            "region_id": self.region_id,
            "statements": list(self.statements),
            "total_statement_count": self.total_statement_count,
            "has_more": self.has_more,
        }
