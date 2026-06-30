"""DC1 Cortex Compiler boundary for Dream Geometry V2.

Allowed: strict structured Growth Proposal and Query Probe compilation.
Forbidden: fact confirmation, natural-language parsing, placement, Field
mutation, recall production, OpenClaw access, runtime calls, or databases.
"""

from .compiler import compile_growth, compile_query
from .errors import DC1Rejection
from .store import CompileGrowthResult, CortexStore, open_store
from .types import (
    CONTRACT_VERSION,
    AxisRay,
    CompilationBudget,
    CompilationDecision,
    CompilationReceipt,
    CompiledGrowthProposal,
    CompiledQueryProbe,
    GrowthStep,
    RuleReference,
    StepReference,
    TextSpanRef,
    canonical_json,
    canonical_payload,
    payload_fingerprint,
)

__all__ = [
    "CONTRACT_VERSION",
    "AxisRay",
    "CompilationBudget",
    "CompilationDecision",
    "CompilationReceipt",
    "CompileGrowthResult",
    "CompiledGrowthProposal",
    "CompiledQueryProbe",
    "CortexStore",
    "DC1Rejection",
    "GrowthStep",
    "RuleReference",
    "StepReference",
    "TextSpanRef",
    "canonical_json",
    "canonical_payload",
    "compile_growth",
    "compile_query",
    "open_store",
    "payload_fingerprint",
]
