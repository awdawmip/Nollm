# DF1 Baseline Report

- current_commit: `0807ba597afa6062f0a9a3aadb8a10cf8caafe55`
- python_version: `3.14.6`
- command: `python validation/df1/run_df1_baseline.py --output C:\Users\chaos\nollm\validation\df1\DF1_BASELINE_REPORT.md`
- admission_manifest: `adm_df1_alpha`, `adm_df1_beta`, `adm_df1_gamma`
- snapshot_semantic_fingerprint: `sha256:605124dab0744a160c3fa4948c2768e9c2c22401e49216944712149ee5f74dee`
- geometry_profile_id: `da1_sealed_default_v1`
- field_policy_identity: `da1_sealed_default_v1|dg2_cover_policy:cover_policy:v2:a2d647c2e140e8629ddf4fa1352e8bda|dg2_gravity_policy:1`
- canonical_trace_count: `12`
- canonical_cover_count: `1`
- verified_link_count: `0`
- gravity_snapshot_summary: `gravity_snapshot:v2:066853500ded9ca83dde291e1019b0e1`
- permutation_invariant: `True`
- no_write_tree_comparison: `pass`

## Acceptance Matrix

- A-001 single legal admission: `pass`
- A-002 two same-chart admissions: `pass`
- A-003 input permutation invariant: `pass`
- A-004 three input permutation invariant: `pass`
- A-005 discard is no-write: `pass`
- B-001 duplicate admission rejects: `pass`
- B-002 fingerprint conflict rejects: `pass`
- B-003 placement fingerprint tamper rejects: `pass`
- B-004 projection fingerprint tamper rejects: `pass`
- B-005 missing shard rejects: `pass`
- B-006 missing/non-accepted proposal rejects: `pass`
- B-007 replay failure rejects: `pass`
- C-001 geometry profile mismatch rejects: `pass`
- C-002 field policy mismatch rejects: `pass`
- C-003 verified cross-chart link retained: `pass`
- C-004 unverified link rejects: `pass`
- C-005 duplicate link canonicalized: `pass`
- C-006 cover/link permutation invariant: `pass`
- D-001 duplicate input is rejected: `pass`
- D-002 same shard different admissions keep provenance: `pass`
- D-003 duplicate cover support uses unique admission set: `pass`
- D-004 usage state is not rewritten: `pass`
- D-005 interpretation/revision not fabricated: `pass`
- E-001 explicit input does not need DF1 discovery: `pass`
- E-002 owner trees unchanged: `pass`
- E-003 no durable snapshot/cache: `pass`
- E-004 import hygiene: `pass`
- E-005 static forbidden path scan: `pass`
- F-001 DR1 validator accepts universe view: `pass`
- F-002 resolve is not called: `pass`
- F-003 universe provenance traces to admissions: `pass`

## Boundary Statement

DF1 validates finite host-supplied admission assembly only. It is not global PB-scale admission discovery, persistent field storage, runtime recall, Query integration, OpenClaw integration, cache, database, network, LLM, NLP, embedding, or anchor recall.
