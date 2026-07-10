# GRF7R Evidence Integrity Report

Overall: `GRF7_ACCEPTED`

Cross-platform portability was not validated in this stage.

## Gate A

Status: `GATE_A_PASS`
Raw: `verifier/computed_gate_framework`
Events: `5`

- `raw inputs present`: measured `5`, required `eq 5`, pass `true`
- `negative control coverage`: measured `4`, required `ge 4`, pass `true`

## Gate B

Status: `GATE_B_PASS`
Raw: `core_integrity/core_integrity_metrics.json`
Events: `100000`

- `100K directory`: measured `100000`, required `ge 100000`, pass `true`
- `indexed lookup descriptors`: measured `1`, required `le 1`, pass `true`
- `directory replay`: measured `True`, required `eq True`, pass `true`
- `identity conflict rejected`: measured `True`, required `eq True`, pass `true`
- `shared route cardinality`: measured `2`, required `ge 2`, pass `true`

## Gate C

Status: `GATE_C_PASS`
Raw: `real_global/real_global_metrics.json`
Events: `20000`

- `persisted placement count`: measured `10000000`, required `eq 10000000`, pass `true`
- `all identity hashes`: measured `10000000`, required `eq 10000000`, pass `true`
- `query count`: measured `20000`, required `eq 20000`, pass `true`
- `cross queries`: measured `5000`, required `ge 5000`, pass `true`
- `stitch queries`: measured `5000`, required `ge 1000`, pass `true`
- `rejection rollback queries`: measured `1000`, required `ge 1000`, pass `true`
- `fallback hashes`: measured `20000`, required `eq 20000`, pass `true`
- `raw query ledger`: measured `20000`, required `eq 20000`, pass `true`
- `bounded hydration`: measured `2`, required `le 2`, pass `true`
- `semantic replay`: measured `True`, required `eq True`, pass `true`

## Gate D

Status: `GATE_D_PASS`
Raw: `real_global/stitch_event_ledger.json`
Events: `208`

- `stitch counts reproduce`: measured `{'proposal_count': 103, 'accepted_count': 101, 'rejected_count': 1, 'deferred_count': 1, 'decayed_count': 1, 'rollback_count': 1}`, required `eq {'accepted_count': 101, 'decayed_count': 1, 'deferred_count': 1, 'proposal_count': 103, 'rejected_count': 1, 'rollback_count': 1}`, pass `true`
- `valid bridge recalled`: measured `True`, required `eq True`, pass `true`
- `rejected bridge inactive`: measured `True`, required `eq True`, pass `true`
- `decayed bridge inactive`: measured `True`, required `eq True`, pass `true`
- `rollback cleanup`: measured `True`, required `eq True`, pass `true`
- `evidence unchanged`: measured `True`, required `eq True`, pass `true`

## Gate E

Status: `GATE_E_PASS`
Raw: `core_integrity/core_integrity_metrics.json`
Events: `7`

- `move changed directory`: measured `True`, required `eq True`, pass `true`
- `move identity`: measured `True`, required `eq True`, pass `true`
- `fallback preserved`: measured `True`, required `eq True`, pass `true`
- `profile atomic rejection`: measured `True`, required `eq True`, pass `true`
- `merge replay equivalence`: measured `True`, required `eq True`, pass `true`
- `merge identities`: measured `True`, required `eq True`, pass `true`
- `no dangling bridge`: measured `True`, required `eq True`, pass `true`

## Gate F

Status: `GATE_F_PASS`
Raw: `runtime/runtime_semantics_metrics.json`
Events: `10`

- `post commit retries`: measured `3`, required `ge 3`, pass `true`
- `retry identities`: measured `True`, required `eq True`, pass `true`
- `cache deletion`: measured `True`, required `eq True`, pass `true`
- `replay restart`: measured `True`, required `eq True`, pass `true`
- `all attacks rejected`: measured `10`, required `eq 10`, pass `true`
- `adapter not truth`: measured `False`, required `eq False`, pass `true`

## Gate G

Status: `GATE_G_PASS`
Raw: `long_running/long_running_metrics.json`
Events: `1000000`

- `one million operations`: measured `1000000`, required `ge 1000000`, pass `true`
- `all operation classes`: measured `True`, required `eq True`, pass `true`
- `majority contract dispatch`: measured `611250`, required `ge 500001`, pass `true`
- `snapshot files`: measured `True`, required `eq True`, pass `true`
- `snapshot replay`: measured `True`, required `eq True`, pass `true`
- `recoveries`: measured `3750`, required `eq 3750`, pass `true`
- `no evidence loss`: measured `0`, required `eq 0`, pass `true`
- `no orphans`: measured `0`, required `eq 0`, pass `true`
- `no collisions`: measured `0`, required `eq 0`, pass `true`
- `memory explained`: measured `True`, required `eq True`, pass `true`

## Gate H

Status: `GATE_H_PASS`
Raw: `workflow/workflow_metrics.json`
Events: `20`

- `four workflows`: measured `4`, required `eq 4`, pass `true`
- `five models`: measured `5`, required `eq 5`, pass `true`
- `false relation injected`: measured `True`, required `eq True`, pass `true`
- `false bridge before rollback`: measured `True`, required `eq True`, pass `true`
- `false bridge after rollback`: measured `False`, required `eq False`, pass `true`
- `rollback success`: measured `True`, required `eq True`, pass `true`
- `bounded conclusion`: measured `observed_on_current_fixture_only`, required `eq observed_on_current_fixture_only`, pass `true`

## Gate I

Status: `GATE_I_PASS`
Raw: `platform/windows_clean_clone.json`
Events: `4`

- `windows process backend`: measured `windows_GetProcessMemoryInfo`, required `eq windows_GetProcessMemoryInfo`, pass `true`
- `current RSS measured`: measured `28389376`, required `gt 0`, pass `true`
- `peak RSS measured`: measured `28393472`, required `ge 28389376`, pass `true`
- `windows tests`: measured `True`, required `eq True`, pass `true`

## Gate J

Status: `GATE_J_PASS`
Raw: `GRF7R_EXTERNAL_ARTIFACT_MANIFEST.json`
Events: `3`

- `external artifacts`: measured `True`, required `eq True`, pass `true`
- `windows clean clone`: measured `True`, required `eq True`, pass `true`
- `clean clone commit ancestor`: measured `True`, required `eq True`, pass `true`
