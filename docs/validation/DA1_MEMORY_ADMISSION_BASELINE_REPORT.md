# DA1 Memory Admission Baseline Report

Status: generated from synthetic DA1 fixture.

## Stable Input IDs

- admission_id: `adm_da1_synthetic_weather`
- shard_id: `shard:da1:synthetic-weather`
- proposal_id: `gp_da1_synthetic_weather`
- plan_id: `apl_da1_synthetic_weather`
- field_profile_id: `da1_sealed_default_v1`

## Zero-Write Preflight

- before_manifest_counts: `{'evidence': 2, 'cortex': 1, 'admission': 1}`
- after_preflight_manifest_counts: `{'evidence': 2, 'cortex': 1, 'admission': 1}`
- zero_write: `True`
- preview_projection_fingerprint: `sha256:b7b579441c199848974ac83b62867e13e9c9c8caf7bef61ee085d1ccdc2d1a76`

## Complete Admission

- outcome: `committed`
- receipt_id: `cr_d745234eacde475331531599cbbe5b3a`
- request_fingerprint: `sha256:f001a414c964ea8053fdb7e06df5ee839197c80d139e16801debcf2ae447cc38`
- placement_plan_fingerprint: `sha256:fa49c5e8aaf023b7a45f2c94bfa567d505399f0181166a759f35f3a802a781ec`
- projection_fingerprint: `sha256:b7b579441c199848974ac83b62867e13e9c9c8caf7bef61ee085d1ccdc2d1a76`
- source_trace_count: `2`
- derived_trace_count: `2`
- residual_count: `2`
- cover_state_counts: `{'candidate': 0, 'stable': 1, 'crystallized': 0}`

## Retry And Replay

- idempotent_retry_outcome: `idempotent`
- idempotent_retry_same_fingerprint: `True`
- replay_same_projection: `True`
- replay_source_trace_ids: `('trace:3f3b9252e43151495f382430088a5287', 'trace:e9d5da042e52db3f4a7e2f09fc5d990d')`
- replay_derived_trace_ids: `('trace:v2:c54801c21df2bad7e06fac802631bc85', 'trace:v2:ee78a54ef4e4976db5fec6d4cdcb914f')`
- replay_residual_ids: `('trace_residual:v2:170bcfb4849115830970d3420710813c', 'trace_residual:v2:ab720f428e821ce9f07d376659a45b51')`
- replay_cover_ids: `('cover:v2:79918f172e4d2529b27d826f339ae1a7',)`

## Public Receipt Redaction

- receipt_keys: `('admission_id', 'compilation_receipt_id', 'cover_state_counts', 'derived_trace_count', 'outcome', 'projection_fingerprint', 'proposal_id', 'residual_count', 'source_trace_count', 'subject_shard_id')`
- forbidden_internal_fields_exposed: `False`

## Report Regeneration

- command: `python -m nollm.dream_geometry.validation.da1_memory_admission_report --output <path>`
