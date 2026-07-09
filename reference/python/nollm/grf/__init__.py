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
]
