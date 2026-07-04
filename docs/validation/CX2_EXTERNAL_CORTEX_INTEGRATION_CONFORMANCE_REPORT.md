# CX2 External Cortex Integration Conformance Report

本报告是 CX2 validation-only conformance report。它证明固定 fixtures、validator 和报告生成可重放；不表示 CX2 已实现 runtime、OpenClaw 接入、自动 admission、global discovery 或真实 memory 写入。

## Protocol

- plan kind: `nollm_cortex_action_plan`
- plan version: `1`
- conformance package: validation-only, declaration-only, no runtime registration
- fixture inventory: 4 valid plans, 10 invalid plans, 1 DG7 correspondence fixture

## Valid Fixtures

- `CX2-VALID-01`: intent `capture_only`, captures `1`, admission requests `0`, recall `false`
- `CX2-VALID-02`: intent `mixed_explicit`, captures `2`, admission requests `2`, recall `true`
- `CX2-VALID-03`: intent `capture_only`, captures `1`, admission requests `0`, recall `false`
- `CX2-VALID-04`: intent `mixed_explicit`, captures `2`, admission requests `2`, recall `true`

## Invalid Fixtures

- `CX2-INVALID-01` rejected with `CX2_FORBIDDEN_AUTOMATION`
- `CX2-INVALID-02` rejected with `CX2_INVALID_PROMOTION`
- `CX2-INVALID-03` rejected with `CX2_INVALID_ADMISSION_REQUEST`
- `CX2-INVALID-04` rejected with `CX2_INVALID_EXPLICIT_ASSEMBLY`
- `CX2-INVALID-05` rejected with `CX2_INVALID_RECALL_REQUEST`
- `CX2-INVALID-06` rejected with `CX2_FORBIDDEN_AUTOMATION`
- `CX2-INVALID-07` rejected with `CX2_FORBIDDEN_AUTOMATION`
- `CX2-INVALID-08` rejected with `CX2_FORBIDDEN_AUTOMATION`
- `CX2-INVALID-09` rejected with `CX2_FORBIDDEN_DG6_INFERENCE`
- `CX2-INVALID-10` rejected with `CX2_INVALID_PLAN`

## Rejection Reason Codes

- `CX2_FORBIDDEN_AUTOMATION`
- `CX2_FORBIDDEN_DG6_INFERENCE`
- `CX2_INVALID_ADMISSION_REQUEST`
- `CX2_INVALID_EXPLICIT_ASSEMBLY`
- `CX2_INVALID_PLAN`
- `CX2_INVALID_PROMOTION`
- `CX2_INVALID_RECALL_REQUEST`

## DG7 Correspondence

- DG7 A/B/C/D is used only as an accepted finite positive-chain correspondence witness.
- A/B correspond to host-declared admitted assembly IDs; C remains captured-only; D remains admitted but unassembled.
- DG6 remains view-only and cannot filter, rank, replace, or influence DR1/DI1 recall.
- CX2 does not expose DG7 as an external model runtime and does not run the DG7 runner.

## Canonical Hashes

- hash origin: canonical JSON emitted by CX2 serialization with sorted keys, compact separators, ASCII, and LF line endings
- valid fixture summary SHA-256: `2babdd5d2a1600919bf0fb878827ff486ce416362edd1cafd7e5a8525e683d78`
- invalid fixture result SHA-256: `267aba4f9e05022f31874d48354625890307fc1e1afd7c3c2152456bf9cc5cc6`
- DG7 correspondence fixture SHA-256: `737f492d6ae519a251a3d5f4c85cb960eafa622c5b474481b6ca2aaf4e2aef16`

## Explicit Non-Goals

- no production runtime, session manager, daemon, scheduler, CLI registration, OpenClaw connection, network, database, or cache
- no LLM/NLP, embedding, semantic search, automatic summary, automatic admission, automatic placement, automatic anchor, or global discovery
- no durable FieldSnapshot, AdmissionRecord, RecallUniverse, ledger event, recall result, or true memory write
- no DG6 recall influence and no DG7 runtime exposure
