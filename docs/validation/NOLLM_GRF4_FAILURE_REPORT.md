# NOLLM GRF4 Failure Recovery Report

The production runner executed the established GRF failure injections while
retaining cached Core behavior:

| Failure | Executed Result | Recovery Boundary |
| --- | --- | --- |
| Density overload | `migration_candidate`, deferred | local cell pressure |
| Wrong placement | revision and re-placement | original and revised cells |
| False stitch | proposal rejected, bridge removed | no bridge remains in rebuilt field |

The runner reported `incremental_update_preserved = true` and
`source_fallback_preserved = true` after the optimized field path. No cache
changed a recall result or source fallback reference.
