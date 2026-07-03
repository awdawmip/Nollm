# DX2 Multi-Admission Assembly-to-Recall Baseline Report

- baseline: `7fb0149ed9b182c7a09b1c7ba9f42f5f12afe009`
- validation_head: `runtime-generated; exact delivery HEAD is reported outside this self-contained report`
- scope: synthetic validation only; no production implementation changes.
- input source: BA1 member receipt admission IDs only.

## Synthetic Object Set

- A/B admitted shard ids: `shard:ci1:8938c946b9e444d87ab39d525d38ea2b, shard:ci1:6e073bfcb681555f3b1e06d9e36c83d2`
- C captured/deferred control shard id: `shard:ci1:b948b8c0c195dd5f47fbc5930043af44`
- D independently admitted but excluded shard id: `shard:ci1:abc2755f00d181a04c61afd674dc98d2`
- BA1 receipt admission ids: `adm_dx2_a, adm_dx2_b`
- D admission id outside explicit set: `adm_dx2_unrelated_d`

## Evidence

- dx2_01: PASS - CI1 capture/deferred A/B/C/D, BA1 committed A/B, C has no AdmissionRecord, capture state unchanged by BA1/DA1.
- dx2_02: PASS - A/B AdmissionRecords replay independently to their own DreamShard, proposal, traces, and placement payload.
- dx2_03: PASS - DF1 input is exactly the BA1 receipt admission id set; reversed input order keeps snapshot and universe identity stable.
- dx2_04: PASS - DR1 recall resolves only admitted explicit-set DreamShards and reads original DreamShard content.
- dx2_05: PASS - DI1 returns a read-only public envelope with request_id echo and no internal ids for field, cover, gravity, chart, placement, source traces, or debug state.
- dx2_06: PASS - C miss semantics: 当前显式 AdmissionRecord / FieldSnapshot 范围内，没有满足条件的正式几何证据。
- dx2_07: PASS - D is present in admission store, carries a real cross-chart VerifiedChartLink, and is absent from snapshot, universe, recall, and DI1 envelope.
- dx2_08: PASS - missing AdmissionRecord and empty explicit DF1 set fail before any replacement by C/D and leave stores unchanged.
- dx2_09: PASS - incomplete DI1 read context returns public DI1_INVALID_READ_CONTEXT without writes.

## Read-Only State

- assembly read-only manifest stable: `True`
- final state manifest entries: `31`

## Recall / DI1 Snapshot

- DR1 status: `resolved`
- DR1 item shard ids: `shard:ci1:6e073bfcb681555f3b1e06d9e36c83d2, shard:ci1:8938c946b9e444d87ab39d525d38ea2b`
- C probe status: `insufficient_evidence`
- C probe item count: `0`
- DI1 ok: `True`
- DI1 primary shard ids: `shard:ci1:6e073bfcb681555f3b1e06d9e36c83d2, shard:ci1:8938c946b9e444d87ab39d525d38ea2b`
- D VerifiedChartLink count: `2`

## Boundary

- No LLM, NLP, embedding, semantic search, global discovery, runtime, OpenClaw, CLI, network, database, cache, session, or real memory integration is used.
- FieldSnapshot and RecallUniverse are call-local in-memory values; no durable field, assembly, or recall directories are created.
- The DX2 A/B finite assembly is single-gravity-chart because sealed DF1 rejects multi-gravity-chart snapshots; D covers VerifiedChartLink as an admitted but excluded control.
