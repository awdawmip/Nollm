"""GRF V3 prototype math kernel."""

from .axial import AxialCoord, CubeCoord, axial_to_cube, cube_to_axial, hex_distance, hex_neighbors, hex_ring
from .cell_address import CellAddress
from .coverage_template import (
    CoverageTemplate,
    CoverageTemplateCompiler,
    KernelEntry,
    expand_lateral,
    expand_template,
)
from .eisenstein import EisensteinInt
from .evidence_island import EvidenceIsland, EvidenceShardRef
from .fixed_point import Q16_ONE
from .local_patch import LocalPatch
from .placement import GeometryMark, PlacementCandidate, PlacementDecision, PlacementRecord, RejectionRecord
from .profiles import Profile, get_profile, performance_profile, profiles
from .bridge_kernel import BridgeKernel
from .admission import MinimalAdmissionRecord
from .propagation import ActivationFrontier, SparseActivation
from .recall import QueryProbe, RecallBudget, resolve_grf_recall
from .recall_digest import CoverageReport, RecallDigest, RecallPath
from .relation_field import RelationField
from .storage import GRFFileStore
from .json_canonical import canonical_dumps, canonical_loads, sha256_canonical
from .ledger import GRFLedger, GRFLedgerEvent
from .replay import load_all_grf_objects, rebuild_relation_field_from_files, replay_recall
from .stitching import StitchProposal, StitchRecord, StitchTransform, StitchWitness

__all__ = [
    "AxialCoord",
    "CellAddress",
    "CoverageTemplate",
    "CoverageTemplateCompiler",
    "CubeCoord",
    "EisensteinInt",
    "EvidenceIsland",
    "EvidenceShardRef",
    "KernelEntry",
    "LocalPatch",
    "GeometryMark",
    "MinimalAdmissionRecord",
    "PlacementCandidate",
    "PlacementDecision",
    "PlacementRecord",
    "Profile",
    "Q16_ONE",
    "RejectionRecord",
    "BridgeKernel",
    "ActivationFrontier",
    "CoverageReport",
    "QueryProbe",
    "RecallBudget",
    "RecallDigest",
    "RecallPath",
    "RelationField",
    "GRFFileStore",
    "GRFLedger",
    "GRFLedgerEvent",
    "SparseActivation",
    "StitchProposal",
    "StitchRecord",
    "StitchTransform",
    "StitchWitness",
    "axial_to_cube",
    "cube_to_axial",
    "expand_lateral",
    "expand_template",
    "get_profile",
    "hex_distance",
    "hex_neighbors",
    "hex_ring",
    "performance_profile",
    "profiles",
    "resolve_grf_recall",
    "canonical_dumps",
    "canonical_loads",
    "load_all_grf_objects",
    "rebuild_relation_field_from_files",
    "replay_recall",
    "sha256_canonical",
]
