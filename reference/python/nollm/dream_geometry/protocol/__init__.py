"""Protocol contracts for Dream Geometry V2.

Allowed: stable enums, immutable ownership records, dependency rules, and
invariant identifiers.
Forbidden: geometry calculation, natural language understanding, runtime calls,
card I/O, memory I/O, or adapter registration.
"""

from .contracts import (
    ChartTransformState,
    CoverState,
    DA1_ADMISSION_INVARIANTS,
    DE1_MEMORY_SUBSTRATE_INVARIANTS,
    DG2_FIELD_INVARIANTS,
    DependencyRule,
    GrowthBasis,
    INVARIANTS,
    InterpretationAuthoringMode,
    InterpretationKind,
    Invariant,
    KernelDirection,
    LedgerEventKind,
    ModuleName,
    OBJECT_OWNERSHIP,
    ObjectKind,
    ObjectOwnership,
    OriginKind,
    RevisionRelation,
    UsageState,
)
from .dependency_rules import ALLOWED_DEPENDENCIES, FORBIDDEN_DEPENDENCIES, is_dependency_allowed

__all__ = [
    "ALLOWED_DEPENDENCIES",
    "FORBIDDEN_DEPENDENCIES",
    "ChartTransformState",
    "CoverState",
    "DA1_ADMISSION_INVARIANTS",
    "DE1_MEMORY_SUBSTRATE_INVARIANTS",
    "DG2_FIELD_INVARIANTS",
    "DependencyRule",
    "GrowthBasis",
    "INVARIANTS",
    "InterpretationAuthoringMode",
    "InterpretationKind",
    "Invariant",
    "KernelDirection",
    "LedgerEventKind",
    "ModuleName",
    "OBJECT_OWNERSHIP",
    "ObjectKind",
    "ObjectOwnership",
    "OriginKind",
    "RevisionRelation",
    "UsageState",
    "is_dependency_allowed",
]
