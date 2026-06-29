"""Protocol contracts for Dream Geometry V2.

Allowed: stable enums, immutable ownership records, dependency rules, and
invariant identifiers.
Forbidden: geometry calculation, natural language understanding, runtime calls,
card I/O, memory I/O, or adapter registration.
"""

from .contracts import (
    ChartTransformState,
    CoverState,
    DG2_FIELD_INVARIANTS,
    DependencyRule,
    GrowthBasis,
    INVARIANTS,
    Invariant,
    KernelDirection,
    ModuleName,
    OBJECT_OWNERSHIP,
    ObjectKind,
    ObjectOwnership,
)
from .dependency_rules import ALLOWED_DEPENDENCIES, FORBIDDEN_DEPENDENCIES, is_dependency_allowed

__all__ = [
    "ALLOWED_DEPENDENCIES",
    "FORBIDDEN_DEPENDENCIES",
    "ChartTransformState",
    "CoverState",
    "DG2_FIELD_INVARIANTS",
    "DependencyRule",
    "GrowthBasis",
    "INVARIANTS",
    "Invariant",
    "KernelDirection",
    "ModuleName",
    "OBJECT_OWNERSHIP",
    "ObjectKind",
    "ObjectOwnership",
    "is_dependency_allowed",
]
