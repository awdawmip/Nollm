# HX1 Trusted Host Staged Execution Report

## Scope

HX1 validates one CX2 CortexActionPlan plus host explicit bindings and executes a trusted internal staged workflow over one finite work-root. It is not OpenClaw, an external API, an agent runtime, automatic memory, global discovery, semantic search, cache, database, network, LLM, NLP, or daemon work.

## Scenario Inventory

- HX1-01 mixed explicit A/B/C with pre-existing admitted D: completed
- HX1-02 capture-only: covered by pytest
- HX1-03 admission-only: covered by pytest
- HX1-05 zero-write preflight rejection: covered by pytest
- HX1-06 partial outcome after capture: covered by pytest
- HX1-07 idempotent reopen: completed
- HX1-08 DG6 strict non-influence: completed by before/after DI1 equality guard

## Results

- completed outcome count: 1
- partial outcome count: covered by pytest
- rejected outcome count: covered by pytest
- receipt status: completed
- completed stages: capture, admission, assembly, recall
- admission receipt ids: adm_hx1_a, adm_hx1_b
- explicit assembly ids: adm_hx1_a, adm_hx1_b
- snapshot source ids: adm_hx1_a, adm_hx1_b
- C captured/deferred isolation: not present in snapshot or recall envelope
- D pre-existing admitted/unassembled isolation: D was admitted before Stage M and is not present in Stage M admission receipts, snapshot, or recall envelope
- DG6 projection id: snapshot_compaction_projection:dg6:92a6f5e9940140f695e104aa3826bc15
- recall envelope status: resolved
- idempotent reopen: canonical mapping identical
- forbidden output directories: none
- canonical receipt fingerprint: sha256:f2cc85deaf6d3a7f0766d31107d58f6632e177257ba1838eb1bc8b0d336a865c
- execution input fingerprint: sha256:f3eb313a3322e30bbc27041ad8ad5352fec18c3f227325b689e2ad8a64a4cf93
- canonical receipt sha256: 2c198c47308612c0427070facc098f16835aa56eedf53b72f53bb7771c859070

## Commands

- `python -m pytest -q reference/python/tests/test_hx1_trusted_host_bridge.py reference/python/tests/test_hx1_host_binding_preflight.py reference/python/tests/test_hx1_staged_outcomes.py reference/python/tests/test_hx1_receipt_regeneration.py reference/python/tests/test_hx1_boundaries.py`
- `python validation/hx1/run_hx1_validation.py --output validation/hx1/HX1_TRUSTED_HOST_STAGED_EXECUTION_REPORT.md`

## Non-Goals

HX1 does not implement OpenClaw, runtime integration, network service, LLM/NLP calls, embeddings, vector search, automatic admission, GrowthProposal generation, PlacementPlan generation, global admission discovery, cache, database, session manager, daemon, or durable global field persistence.
