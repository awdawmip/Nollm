# DG7 Delivery Receipt

- phase: `DG7`
- root baseline: `47eca074045cede79d19b897ff4cae48dca23ab6`
- branch: `codex/dg7-explicit-reference-runtime-positive-verification`
- delivery commit: final DG7 commit recorded in delivery response

## Phase 0 Promotion

- previous main: `5e91504d0f3961be9631856a8853a58ca6bd1921`
- accepted DG6: `47eca074045cede79d19b897ff4cae48dca23ab6`
- main = origin/main = `47eca074045cede79d19b897ff4cae48dca23ab6` after fast-forward
- DG7 branch was created from accepted DG6.
- DG7 itself was not merged into main.

## Boundary

DG7 adds a validation-only explicit reference runtime positive verification path.

It runs a fixed A/B/C/D scenario through real public CI1 capture, BA1 batch admission, DA1 admission, DF1 finite assembly, DG6 view-only projection, DR1 recall, and DI1 public envelope.

DG7-C1 binds DF1 finite assembly to `DG7ReferenceScenario.explicit_assembly_admission_ids`. BA1 observed admission IDs must exactly equal the host-declared tuple before DF1 assembly; D remains excluded because it is not in the declaration, not because the runner derived a set from BA1 output.

It does not implement production runtime integration, OpenClaw, CLI registration, network service, automatic admission, LLM/NLP, semantic search, persistent compaction, cache, database, global discovery, or performance claims.

## Subagents

- Public-route scout: read-only review of CI1/BA1/DA1/DF1/DG6/DR1/DI1 public APIs, DX2 fixture semantics, work-root side effects, and objects DG7 must not fake.
- Reference runner implementer: main agent implemented `nollm.dream_geometry.validation.dg7` and `reference/python/scripts/run_dg7_reference_runtime.py`.
- Validation/report implementer: main agent implemented DG7 tests and validation report runner.
- Documentation reviewer: main agent implemented protocol, validation report, delivery receipt, and ROADMAP update.

## Verification Scope

- A/B are captured, deferred, host-promoted, admitted, assembled, projected, recalled, and exposed through DI1 public evidence.
- C is captured/deferred only and excluded from AdmissionRecord, DF1 snapshot, DG6 projection, DR1 recall, and DI1 envelope.
- D is admitted but excluded from the explicit DF1 finite set and therefore excluded from the current snapshot, projection, recall, and envelope.
- DG7-C1 rejects D-only, duplicate, missing, reordered, and invalid explicit assembly declarations before DF1 assembly.
- C captured-only absence is accepted only when `get_admission_record` raises `FileNotFoundError`; other lookup failures are structured DG7 admission errors.
- DG6 projection validates lossless expansion and does not affect DI1 recall.
- Repeated fresh Python processes produce byte-identical canonical receipts.
- Same owned work root reopens by returning the cached DG7 receipt without replaying DA1 writes or changing the work-root manifest.
- Error paths for unknown scenario, missing output, foreign work root, and invalid explicit set are structured DG7 failures without Python traceback.
