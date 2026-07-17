# CAOLD DC1 Recall Lens Asset Reuse Report

Date: 2026-07-17

## Classification

| DC1 asset | V3.11 classification | Use |
|---|---|---|
| axis/ray and growth/query duality | `REUSE_CONCEPT` | Teach operation-local future Recall perspectives and validate placement/recall cycle consistency. |
| Evidence basis spans | `REUSE_CONCEPT` | Require exact Capture role, offsets, and quoted bytes for every Recall Lens. |
| relative-time discipline and fixtures | `PORT_WITH_SIMPLIFICATION` | Resolve Capture-relative language once from its reference instant and timezone; persist only the self-contained Statement. |
| Query Probe fixtures | `PORT_WITH_SIMPLIFICATION` | Supply Lab contrast cases without restoring a production query compiler. |
| bounded ray budgets | `PORT_WITH_SIMPLIFICATION` | Limit each Statement to four Lenses, each Lens to four Locality IDs, and each plan to three contacts. |
| `RESERVED_AXES`, rule references, receipts, and multi-step `GrowthStep` chains | `REFERENCE_ONLY` | Historical comparison only. |
| Cortex Store and durable growth proposals | `REFERENCE_ONLY` | No V3.11 runtime dependency or write path. |
| persistent axes, topics, query routes, or fact-to-entry maps | `DELETE_ACTIVE` | Forbidden from active V3.11 production paths. |

## Boundary Verification

Production V3.11 code does not import `nollm.dream_geometry.cortex`, create a Cortex Store, persist a Recall Lens, or expose fixed semantic axes. The reused contract is deliberately smaller: exact Evidence-backed basis spans plus bounded candidate references in one Dream operation. Access validates the wire and Core receives geometry-only Junction requests.

The old DC1 relative-time rule remains instructive but is not copied literally: V3.11 resolves relative language against the immutable Capture reference instant before Statement admission. A later query clock cannot reinterpret that admitted Statement.
