"""DF1 finite FieldSnapshot assembly.

Allowed: replay host-supplied finite AdmissionRecords into an immutable
in-memory FieldSnapshot and DR1-compatible RecallUniverse.
Forbidden: admission discovery, durable writes, recall execution, Query
compilation, runtime integration, or external retrieval paths.
"""

from .builder import assemble_field_snapshot, recall_universe_from_snapshot
from .errors import DF1AssemblyError
from .types import (
    AdmissionManifestEntry,
    AdmissionReplaySource,
    AssemblyAuditSummary,
    FieldAssemblyPolicy,
    FieldAssemblyResult,
    FiniteAdmissionSet,
    FiniteFieldSnapshot,
)

__all__ = [
    "AdmissionManifestEntry",
    "AdmissionReplaySource",
    "AssemblyAuditSummary",
    "DF1AssemblyError",
    "FieldAssemblyPolicy",
    "FieldAssemblyResult",
    "FiniteAdmissionSet",
    "FiniteFieldSnapshot",
    "assemble_field_snapshot",
    "recall_universe_from_snapshot",
]
