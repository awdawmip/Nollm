# DE1.1R Interpretation Subject Domain Closure Delivery Receipt

Date: 2026-06-29

## Scope

- Task: DE1.1R Interpretation Subject Domain Closure.
- Branch: `feature/de1-01r-interpretation-subject-domain`.
- Base HEAD: `a52784a175e64283602ff412891c01b675d8e465`.
- Final HEAD: the commit containing this receipt; authoritative immutable SHA is verified by `git bundle list-heads` after commit creation.
- Boundary: only enforce `InterpretationRecord.subject_shard_id -> DreamShard`. No DG1/DG2, Field, Cortex, Recall, OpenClaw, runtime, adapter, CLI, database, security, interpretation chains, new object types, or true memory work.

## Changed Files

- `docs/delivery/DE1_01R_INTERPRETATION_SUBJECT_DOMAIN_CLOSURE_DELIVERY_RECEIPT.md`
- `docs/evidence/DE1_MEMORY_SUBSTRATE_CONVENTIONS.md`
- `docs/validation/DE1_MEMORY_SUBSTRATE_BASELINE_REPORT.md`
- `protocol/v2/DE1_MEMORY_SUBSTRATE_CONTRACT.md`
- `protocol/v2/INVARIANTS.md`
- `reference/python/nollm/dream_geometry/evidence/store.py`
- `reference/python/nollm/dream_geometry/validation/de1_memory_substrate_report.py`
- `reference/python/tests/test_de1_memory_substrate.py`

## Repair

- `MemorySubstrateStore.put_interpretation()` now checks the subject through the `shards/` bucket only.
- `_validate_store()` uses the same shard-only subject-domain check during reopen.
- Revision members and usage-state targets still accept the existing `DreamShard | InterpretationRecord` domain.

## Test Mapping

- T-365/T-371: `test_de1_1r_t365_t371_interpretation_subject_must_be_shard_and_retry_is_idempotent`.
- T-366: `test_de1_1r_t366_nested_interpretation_write_rejected_without_side_effects`.
- T-367: `test_de1_1r_t367_nested_interpretation_rejected_after_reopen`.
- T-368: `test_de1_1r_t368_on_disk_nested_interpretation_rejected_on_open`.
- T-369/T-370: `test_de1_1r_t369_t370_revision_and_usage_still_accept_interpretation_targets`.
- T-372: targeted DG0/DG1/DG2/DE1 regression, package hygiene, report regeneration.

## Verification Results

- Preflight `git merge-base --is-ancestor a52784a175e64283602ff412891c01b675d8e465 HEAD`: success.
- Preflight `git status --short`: clean.
- Preflight `git log -1 --oneline`: `a52784a1 DE1.1: close epistemic identity and ledger gaps`.
- DE1 focused tests: `35 passed in 3.09s`.
- DG0/DG1/DG2/DE1 targeted suite: `175 passed in 8.07s`.
- `python -m nollm.dream_geometry.validation.de1_memory_substrate_report --output ../../docs/validation/DE1_MEMORY_SUBSTRATE_BASELINE_REPORT.md`: passed and regenerated report with `F-L interpretation subject limited to shard | pass`.
- `python scripts/check_package_hygiene.py ../..`: `PASS package hygiene`.
- `git diff --check`: exit 0; warning only that `docs/validation/DE1_MEMORY_SUBSTRATE_BASELINE_REPORT.md` CRLF will be replaced by LF.
- Sealed path diff against `a52784a175e64283602ff412891c01b675d8e465` for DG1 Geometry, DG2 Field, DG1/DG2 tests, and DG1/DG2 reports: no output.
- `python run_tests.py`: `1060 passed, 183 subtests passed in 344.78s (0:05:44)`.
- Post-cleanup `python scripts/check_package_hygiene.py ../..`: `PASS package hygiene`.

## Git And Bundle Evidence

- Commit message: `DE1.1R: close interpretation subject domain`.
- Push result: recorded after commit in final delivery response.
- Bundle path: `C:\Users\chaos\nollm_de1_01r_interpretation_subject_domain_20260629.bundle`.
- Bundle SHA-256: recorded after bundle creation in final delivery response; checksum only, not a security signature.
- `git bundle verify` and `git bundle list-heads`: recorded after commit in final delivery response.
- `exception_paths`: none.

## Seal

DE1.1R closes the reviewed subject-domain blocker. DE1 is sealed as `Accepted and sealed - Memory Substrate / Epistemic Core`. No further DE1.x work is included or scheduled by this delivery.
