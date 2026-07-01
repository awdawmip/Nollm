# DX1 / DX1.1 Delivery Receipt - Synthetic Memory Cycle Validation

Date: 2026-07-01

Branch: `feature/dx1-end-to-end-synthetic-memory-cycle-validation`

Base sealed commit: `76a4d1ba8b97043ea2c673ca64ab6f816be18a12`

DX1 implementation commit under audit: `e8838d71248d007aae01f15a7dd0c2b45b362f83`

DX1.1 final implementation commit: this receipt is part of the final DX1.1
closure commit; verify the concrete commit with `git log -1 --oneline` and the
single-file bundle `list-heads` recorded at delivery.

## Scope

DX1 validates one synthetic end-to-end memory cycle across sealed public module
APIs. DX1.1 closes validation witness gaps only:

- commit-range sealed implementation scope witness;
- pre-compute K_up / K_down coverage target input permutation;
- Interpretation / Revision tuple input permutation;
- S05 public metadata forbidden-token witness, including `selection_basis`;
- self-contained report and receipt evidence.

DX1.1 does not modify sealed production Geometry, Field, Evidence, Cortex,
Recall, or Adapter implementation modules.

## Changed Paths

- `docs/delivery/DX1_DELIVERY_RECEIPT_20260701.md`
- `docs/validation/DX1_SYNTHETIC_MEMORY_CYCLE_BASELINE_REPORT.md`
- `protocol/v2/DX1_SYNTHETIC_MEMORY_CYCLE_CONTRACT.md`
- `protocol/v2/INVARIANTS.md`
- `reference/python/nollm/dream_geometry/validation/dx1_synthetic_cycle_fixture.py`
- `reference/python/nollm/dream_geometry/validation/dx1_synthetic_cycle_report.py`
- `reference/python/tests/test_dx1_synthetic_memory_cycle_boundaries.py`
- `reference/python/tests/test_dx1_synthetic_memory_cycle_determinism.py`

## Public API Chain

- DE1: `open_store`, `put_dream_shard`, `put_interpretation`,
  `put_revision_thread`, `record_usage_transition`, public readers.
- DC1: `CortexStore.compile_growth`, `compile_query`, stored current proposal
  readback.
- DG1: `make_hex_cell`, `compute_distribution`.
- DG2: `TraceSeed`, `seed_to_trace`, `propagate_trace`, `build_local_covers`,
  `calculate_gravity_snapshot`.
- DR1: `validate_recall_universe`, `resolve_recall`.
- DI1: `IntegrationShell.handle`.

## Scenario Results

- S01 complete synthetic cycle resolves one primary target: pass.
- S02 missing runtime relative-time resolution defers without evidence: pass.
- S03 exact mismatch does not recall target: pass.
- S04 retired usage state is context-only: pass.
- S05 public envelope hides internal geometry and private provenance: pass.
- S06 same input rerun is deterministic and persists no recall output: pass.
- S07 pre-compute input permutation keeps public mapping and canonical
  distributions stable: pass.

## Validation Witnesses

- C-701 / C-714 sealed range scope:
  `git diff --name-only 76a4d1ba8b97043ea2c673ca64ab6f816be18a12..HEAD -- reference/python/nollm/dream_geometry/geometry reference/python/nollm/dream_geometry/field reference/python/nollm/dream_geometry/evidence reference/python/nollm/dream_geometry/cortex reference/python/nollm/dream_geometry/recall reference/python/nollm/dream_geometry/adapters`
  produced empty output.
- C-702 K_up multi-target witness: baseline report records max positive target
  kernels as `3`.
- C-703 K_down multi-target witness: baseline report records max positive
  target kernels as `4`.
- C-704 context order witness: tests assert Interpretation and Revision input
  tuples are genuinely reversed before RecallUniverse construction.
- C-705 S07 witness: tests assert public mapping equality, canonical K_up /
  K_down payload equality, primary shard/axes/tier/context equality, and no
  target/distractor selection drift.
- C-706 through C-708 public boundary witness: tests strip only `content` and
  `statement`, keep public metadata including `selection_basis`, assert the
  fixed basis allowlist, and scan non-content public mapping for forbidden
  provenance/internal tokens.
- C-709 report deferred fixture witness: report uses one deferred fixture's
  invocation and context together.
- C-710 report completeness: regenerated baseline report includes base commit,
  API chain, S01-S07, K_up/K_down/traversal, stable cover, gravity internal
  fact, relative-time boundary, public output categories, persistence witness,
  fingerprints, and explicit omissions.
- C-711 receipt evidence: this receipt records concrete commands and results.
- C-712 protocol clarification: DX1 contract and invariants clarify
  commit-range scope and pre-compute input permutation.
- C-713 no persistence: tests assert Evidence/Cortex manifests do not change
  across success, deferred, mismatch, and rerun calls.

## Commands And Results

- `python -m pytest -q reference/python/tests/test_dx1_synthetic_memory_cycle.py reference/python/tests/test_dx1_synthetic_memory_cycle_boundaries.py reference/python/tests/test_dx1_synthetic_memory_cycle_determinism.py reference/python/tests/test_di1_integration_shell_contract.py reference/python/tests/test_di1_integration_shell_public_view.py reference/python/tests/test_dr1_01_closure.py reference/python/tests/test_dc1_cortex_compiler.py reference/python/tests/test_de1_memory_substrate.py reference/python/tests/test_dg2_trace_propagation.py reference/python/tests/test_dg2_cover_lifecycle.py reference/python/tests/test_dg1_coverage_kernels.py reference/python/tests/test_package_hygiene_script.py`
  result: `141 passed in 10.17s`.
- `python -m nollm.dream_geometry.validation.dx1_synthetic_cycle_report --output C:\Users\Administrator\AppData\Local\Temp\dx1_01_report_check.md`
  result: generated report, SHA256 `228A7B1EC68079E658A2B7F525A20F8A2B0264AEAEC9B67E7BDE11577D9B5DFA`.
- `python reference/python/nollm/dream_geometry/validation/dx1_synthetic_cycle_report.py`
  result: regenerated `docs/validation/DX1_SYNTHETIC_MEMORY_CYCLE_BASELINE_REPORT.md`.
- `python reference/python/scripts/check_package_hygiene.py`
  result: `PASS package hygiene`.
- `git diff --check`
  result: exit code 0.
- sealed range scope command above
  result: empty output.
- `python run_tests.py` from `reference/python`
  result: `1152 passed, 183 subtests passed in 532.53s (0:08:52)`.
- `python -m nollm.cli validate ../../examples/openclaw`
  result: `PASS`.
- `python -m nollm.cli audit ../../examples/openclaw`
  result: `validation.pass: true`, `issue_count: 0`.
- `python -m nollm.cli audit-check ../../examples/openclaw --against ../../examples/audit_reports/openclaw_audit.json`
  result: `ok: true`, `matches: true`, `drift_count: 0`.
- `python -m nollm.cli tool ../../examples/tool_requests/audit_openclaw.json`
  result: `ok: true`.
- `python -m nollm.cli tool ../../examples/tool_requests/orient.json`
  result: `ok: true`.
- `python -m nollm.cli tool ../../examples/tool_requests/generated_output_examples/recall_scale_scan.json`
  result: `ok: true`; generated `recall_20260701_000001.json/md` files were removed after the run.
- final hygiene after cleanup:
  result: `PASS package hygiene`.
- final audit-check after cleanup:
  result: `ok: true`, `matches: true`, `drift_count: 0`.

## Bundle Evidence

The single-file Git bundle is generated outside the repository after the final
commit. Delivery must record:

- bundle path;
- `git bundle verify` result;
- `git bundle list-heads` result;
- SHA256 file hash.

## Boundaries And Non-Goals

No LLM, NLP, embedding, semantic search, anchor retrieval, global window
admission, runtime, OpenClaw, CLI integration, network, database, cache,
session, write path, or real memory integration was added.

No sealed production implementation path was modified.

DX1 = Accepted and sealed - End-to-End Synthetic Memory Cycle Validation.
No DX1.2 or additional DX1.x work is opened by this receipt.
