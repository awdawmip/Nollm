"""Pure Field Dynamics boundary for Dream Geometry V2.

Allowed: deterministic Growth Trace propagation, local Coarse Cover views,
internal gravity snapshots, and lossless trace compaction views.
Forbidden: Growth Proposal generation, external gravity exposure, Evidence
replacement, adapter behavior, OpenClaw access, runtime calls, or memory I/O.
"""

from .compaction import compact_traces, expand_compaction
from .cover import build_local_covers, crystallize_cover, evaluate_cover_eligibility
from .gravity import calculate_gravity_snapshot
from .trace import propagate_trace, seed_to_trace
from .types import (
    CoarseCover,
    CoverEligibility,
    CoverPolicy,
    CrystallizationDecision,
    GravityContribution,
    GravityPolicy,
    GravitySnapshot,
    GrowthTrace,
    TraceCompaction,
    TracePropagationResult,
    TraceResidual,
    TraceSeed,
    VerifiedChartLink,
)

__all__ = [
    "CoarseCover",
    "CoverEligibility",
    "CoverPolicy",
    "CrystallizationDecision",
    "GravityContribution",
    "GravityPolicy",
    "GravitySnapshot",
    "GrowthTrace",
    "TraceCompaction",
    "TracePropagationResult",
    "TraceResidual",
    "TraceSeed",
    "VerifiedChartLink",
    "build_local_covers",
    "calculate_gravity_snapshot",
    "compact_traces",
    "crystallize_cover",
    "evaluate_cover_eligibility",
    "expand_compaction",
    "propagate_trace",
    "seed_to_trace",
]
