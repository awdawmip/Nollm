"""Dream Geometry V2 boundary package.

Allowed: name the parallel V2 modules and expose no-runtime scaffolding.
Forbidden: runtime integration, OpenClaw access, memory reads or writes, CLI
registration, geometry recall, card placement, or algorithm execution.
"""

__all__ = [
    "protocol",
    "evidence",
    "geometry",
    "field",
    "cortex",
    "recall",
    "adapters",
    "validation",
]
