from .atom import MemoryAtom
from .bridge import BridgeSpec, GeometryAnchor, Q16_ONE
from .command import (
    BridgeAddCommand,
    BridgeRemoveCommand,
    MoveCommand,
    PutCommand,
    RemoveCommand,
    ReplaceCommand,
)
from .coverage_template import CoverageTemplate, KernelEntry, expand_template, validate_lateral_ring
from .geometry import GeometryAddress
from .handle import AtomHandle
from .incoming_coverage import (
    IncomingCoverage,
    IncomingCoverageMember,
    incoming_coverage,
    incoming_coverage_candidates,
)
from .kernel_registry import KernelRegistry
from .junction import (
    JunctionCandidate,
    JunctionRequest,
    RelationGroupJunctionCandidate,
    RelationGroupJunctionRequest,
    solve_junction_candidates,
    solve_relation_group_junction_candidates,
)
from .physical_coverage import (
    ACTIVE_APPROXIMATION_POLICY,
    AmbiguousPhysicalCoverage,
    ApproximateCoveragePolicy,
    PhysicalCoverageExpansion,
    PhysicalCoverageMember,
    UnsupportedPhysicalCoverage,
    clear_physical_coverage_cache,
    expand_physical_coverage,
)
from .ports import CoreTraceEvent, TraceSink
from .profiles import available_profile_ids, runtime_profile
from .recall import CoreRecallItem, CoreRecallRequest, CoreRecallResult, RecallBudget
from .sampled_geometry import (
    CoverageStencil,
    coverage_stencil_q40,
    coverage_sample_offsets_q40,
    nearest_axial_q40,
    normalize_q16_weights,
)
from .state import CoreRuntime, clear_surface_order_cache
from .surface import (
    CoverageDescentCell,
    CoverageDescentPage,
    PhysicalFieldScope,
    SurfaceAggregateAddress,
    SurfaceCellProjection,
    SurfaceGridSpec,
    SurfaceOrderInfo,
    SurfacePage,
)


__all__ = [
    "AtomHandle",
    "ACTIVE_APPROXIMATION_POLICY",
    "AmbiguousPhysicalCoverage",
    "ApproximateCoveragePolicy",
    "BridgeAddCommand",
    "BridgeRemoveCommand",
    "BridgeSpec",
    "CoreRecallItem",
    "CoreRecallRequest",
    "CoreRecallResult",
    "CoreRuntime",
    "CoreTraceEvent",
    "CoverageTemplate",
    "CoverageStencil",
    "coverage_stencil_q40",
    "coverage_sample_offsets_q40",
    "nearest_axial_q40",
    "normalize_q16_weights",
    "CoverageDescentCell",
    "CoverageDescentPage",
    "PhysicalFieldScope",
    "PhysicalCoverageExpansion",
    "PhysicalCoverageMember",
    "GeometryAddress",
    "GeometryAnchor",
    "IncomingCoverage",
    "IncomingCoverageMember",
    "KernelEntry",
    "KernelRegistry",
    "JunctionCandidate",
    "JunctionRequest",
    "RelationGroupJunctionCandidate",
    "RelationGroupJunctionRequest",
    "MemoryAtom",
    "MoveCommand",
    "PutCommand",
    "Q16_ONE",
    "RecallBudget",
    "RemoveCommand",
    "ReplaceCommand",
    "TraceSink",
    "UnsupportedPhysicalCoverage",
    "SurfaceAggregateAddress",
    "SurfaceCellProjection",
    "SurfaceGridSpec",
    "SurfaceOrderInfo",
    "SurfacePage",
    "expand_template",
    "expand_physical_coverage",
    "incoming_coverage",
    "incoming_coverage_candidates",
    "clear_physical_coverage_cache",
    "clear_surface_order_cache",
    "available_profile_ids",
    "runtime_profile",
    "solve_junction_candidates",
    "solve_relation_group_junction_candidates",
    "validate_lateral_ring",
]
