"""DG5 evidence-preserving trace compaction capability."""

from .errors import CompressionPlanningError
from .planner import plan_trace_compaction
from .types import CompactedTraceView, CompressionPlan, CompressionPolicy
from .validation import validate_compression_plan
from .view import expand_compression_plan

__all__ = [
    "CompactedTraceView",
    "CompressionPlan",
    "CompressionPlanningError",
    "CompressionPolicy",
    "expand_compression_plan",
    "plan_trace_compaction",
    "validate_compression_plan",
]
