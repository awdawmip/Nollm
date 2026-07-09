# Nollm GRF Refoundation

GRF V3 is the new target architecture for the geometry relation field line.
GRF keeps useful V2 principles: deterministic evidence handling, explicit
host boundaries, bounded public surfaces, and auditable validation. The sealed
V2 modules remain historical assets, but they are not hard implementation
boundaries for the GRF refoundation.

GRF1-A implements only R1 and R2:

```text
R1 integer axial/cube cells, Eisenstein integer transforms, Q16 weights, profile registry
R2 offline coverage template compiler and bounded runtime lookup
```

Coverage is the primary relation source in this prototype. Runtime geometry
must be template lookup: no runtime polygon overlap, no trigonometry, no float
scoring for the exact profile, and no object-level semantic edges.

The first performance candidate is `eisenstein_exact_v1`. The aligned profile
is a control baseline. `dream_quasi_v1` is a research profile and must not be
selected as the default performance path.

GRF1-A does not implement EvidenceIsland persistence, LocalPatch,
StitchProposal, StitchRecord, PlacementRecord migration, AdmissionRecord
migration, GRF recall product behavior, OpenClaw runtime, or adapter work.
