# DG2.1 Field Integrity Repair Delivery Receipt

Date: 2026-06-29

## Scope

- Task: DG2.1 Dream Geometry V2 Field Dynamics Integrity Repair.
- Branch: `feature/dg2-01-field-integrity-repair`.
- Base HEAD: `7f604526194d160edf95e8f25f29e7c8d1babf5d`.
- Final HEAD: the commit containing this receipt; authoritative immutable SHA is verified by `git bundle list-heads` after commit creation.
- Boundary: DG2 Field-only repair; no DG1 geometry, V1, OpenClaw, runtime, memory, CLI, adapter, Cortex, Recall, trial, or rollback changes.

## Changed Files

- `docs/delivery/DG2_01_FIELD_INTEGRITY_REPAIR_DELIVERY_RECEIPT.md`
- `docs/field/DG2_FIELD_DYNAMICS_CONVENTIONS.md`
- `docs/validation/DG2_FIELD_DYNAMICS_BASELINE_REPORT.md`
- `protocol/v2/DG2_FIELD_DYNAMICS_CONTRACT.md`
- `protocol/v2/INVARIANTS.md`
- `reference/python/nollm/dream_geometry/field/compaction.py`
- `reference/python/nollm/dream_geometry/field/cover.py`
- `reference/python/nollm/dream_geometry/field/gravity.py`
- `reference/python/nollm/dream_geometry/field/trace.py`
- `reference/python/nollm/dream_geometry/field/types.py`
- `reference/python/nollm/dream_geometry/validation/dg2_field_report.py`
- `reference/python/tests/test_dg2_compaction.py`
- `reference/python/tests/test_dg2_cover_lifecycle.py`
- `reference/python/tests/test_dg2_gravity_snapshot.py`
- `reference/python/tests/test_dg2_trace_propagation.py`

## Defect Repairs

- F-201: `propagate_trace` now materializes every positive DG1 kernel mass instead of skipping sub-tolerance mass. `accounting_error` is computed with `math.fsum` and represents only summation error.
- F-202: `CoverPolicy` rejects relaxed structural floors: `min_independent_support < 2`, `min_axes < 2`, and `max_provisional_mass != 0.0`. Eligibility always treats positive provisional mass as blocking stability.
- F-203: `build_local_covers`, `compact_traces`, and `calculate_gravity_snapshot` reject duplicate identities. `expand_compaction` rejects duplicate or missing manifest IDs.
- F-204: `CoarseCover` records `policy_id`; cover identity includes `policy_id`, `policy_version`, and full policy semantic payload. `evaluate_cover_eligibility` rejects policy identity mismatch.

## Test Mapping

- T-201: `test_dg2_1_t201_tiny_positive_mass_materializes`.
- T-202: `test_dg2_1_t202_policy_cannot_relax_structural_floors`.
- T-203: `test_dg2_1_t203_provisional_never_crystallizes`.
- T-204: `test_dg2_1_t204_duplicate_trace_id_rejected_for_covers`, `test_dg2_1_t204_duplicate_trace_id_rejected_for_compaction`.
- T-205: `test_dg2_1_t205_duplicate_cover_id_rejected`.
- T-206: `test_dg2_1_t206_policy_identity_enters_cover_id`, `test_dg2_1_t206_policy_semantics_enter_cover_id`.
- T-207: `test_dg2_1_t207_policy_mismatch_rejected`.
- T-208: `test_dg2_1_t208_expand_rejects_bad_manifest` plus existing compatible compaction round-trip test.
- T-209: Existing DG2 Trace, Cover, Gravity, Compaction, and boundary tests rerun with DG0/DG1 suite.

## Verification Results

- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q ... DG0/DG1/DG2 target list`: `136 passed in 7.02s`.
- `python scripts/check_package_hygiene.py ../..`: `PASS package hygiene`.
- `python -m nollm.dream_geometry.validation.dg2_field_report --output ../../docs/validation/DG2_FIELD_DYNAMICS_BASELINE_REPORT.md`: passed and regenerated report.
- `python run_tests.py`: `1021 passed, 183 subtests passed in 353.43s (0:05:53)`.
- Post-cleanup `python scripts/check_package_hygiene.py ../..`: `PASS package hygiene`.
- `git diff --check`: exit 0; warning only that `docs/validation/DG2_FIELD_DYNAMICS_BASELINE_REPORT.md` CRLF will be replaced by LF.

## Git And Bundle Evidence

- `git status --short` before commit: only allowed DG2.1 paths modified plus this receipt.
- Commit message: `DG2.1: repair field mass and identity integrity`.
- Push result: recorded after commit in final delivery response.
- Bundle path: `C:\Users\chaos\nollm_dg2_01_field_integrity_repair_20260629.bundle`.
- `git bundle verify` and `git bundle list-heads`: recorded after commit in final delivery response.

## Seal

DG2.1 completes the Field Integrity Repair. DG2 is sealed as `Accepted and sealed - Deterministic Field Dynamics Foundation`. Remaining non-blocking items are DG3+ work; no additional DG2.x hardening is included here.
