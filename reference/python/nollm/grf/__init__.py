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
from .profiles import Profile, get_profile, performance_profile, profiles
from .bridge_kernel import BridgeKernel
from .stitching import StitchProposal, StitchRecord, StitchWitness

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
    "Profile",
    "Q16_ONE",
    "BridgeKernel",
    "StitchProposal",
    "StitchRecord",
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
