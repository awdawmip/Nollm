# NOLLM GRF3R2 Place and Admit Separation

```text
capture -> EvidenceShardRecord
place   -> EvidenceIsland, LocalPatch, PlacementCandidate, PlacementDecision,
           GeometryMark, PlacementRecord
admit   -> MinimalAdmissionRecord for that existing PlacementRecord
```

The host-facing `place` capability never writes an admission record. The
host-facing `admit` capability cannot rerun placement: it requires matching
`EvidenceIdentity` and `PlacementIdentity`, reads that placement, checks its
source fallback, and writes only the resulting admission record.

Recall and replay bind a typed identity to their identity-bearing entry mode
before Core dispatch. Untyped entry modes reject all GRF identity fields.
