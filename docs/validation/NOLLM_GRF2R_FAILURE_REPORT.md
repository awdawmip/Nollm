# NOLLM GRF2R Failure Injection Report

The GRF2R benchmark executes failures against live in-memory field state.

| Injection | Executed Result | Control Boundary |
| --- | --- | --- |
| Density overload | Five actual placements entered one cell with migration threshold four; `density_pressure` became `migration_candidate`. | The benchmark marked the placement flow deferred and surfaced a migration candidate. |
| Wrong placement | An inserted placement was revised and moved from `(0, 0)` to `(99, 99)`. | The original and revised cells are the complete affected region. |
| False stitch | A lexical-only proposal was rejected; a previously inserted bridge was removed before field construction. | The rebuilt `RelationField` had no bridge kernels, proving rollback and bridge decay containment. |

The tests assert these resulting states directly; the report is not a descriptive substitute for execution.
