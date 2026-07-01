# DI1 Delivery Receipt - Integration Shell Foundation

## Scope

Task pack: `NOLLM_DI1_INTEGRATION_SHELL_FOUNDATION_TASK_PACK_20260701.md`.

DI1 adds a transport-neutral, host-controlled, read-only Integration Shell under
`nollm.dream_geometry.adapters`. The shell accepts only typed host-provided
DC1 `CompiledQueryProbe`, DR1 finite `RecallUniverse`, DE1
`MemorySubstrateStore`, optional `RuntimeTimeResolution`, and fixed
`RecallPolicy`, then calls sealed DR1 `resolve_recall` and maps the result into
a public recall envelope.

No Query compilation, RecallUniverse construction, global memory admission,
OpenClaw, runtime, CLI, network, database, cache, session, write path, real
memory hook, or public internal-geometry selector was implemented.

## Baseline

- Start branch: `feature/dr1-01t-evidence-aggregation-closure`
- DI1 branch: `feature/di1-integration-shell-foundation`
- Start base commit: `bfda03bdd458fd5a9cb057b9f8550e52fa3716c6`
- Required sealed commits present in local history:
  - DG1: `314f0d93ce04977588db933969ea71c216351a7b`
  - DG2: `74b00a93b93abd22aadf08988a9d5947992f6e22`
  - DE1: `c2a28c25cb472a8911c8bd8367a27351c6606aec`
  - DC1: `19d516681301ee9213b7591fd36f9775ebb5207e`
  - DR1: `bfda03bdd458fd5a9cb057b9f8550e52fa3716c6`
- Final HEAD: recorded by `git log -1 --oneline`, final handoff, and bundle list-heads after commit creation.

## Changed Paths

- `reference/python/nollm/dream_geometry/adapters/`
- `reference/python/nollm/dream_geometry/validation/di1_integration_fixture.py`
- `reference/python/nollm/dream_geometry/validation/di1_integration_shell_report.py`
- `reference/python/tests/test_di1_integration_shell_*.py`
- `protocol/v2/DI1_INTEGRATION_SHELL_CONTRACT.md`
- DI1 append-only updates to:
  - `protocol/v2/INVARIANTS.md`
  - `protocol/v2/OBJECT_OWNERSHIP.md`
  - `protocol/v2/MODULE_DEPENDENCY_RULES.md`
- `docs/validation/DI1_INTEGRATION_SHELL_BASELINE_REPORT.md`
- `docs/delivery/DI1_DELIVERY_RECEIPT_20260701.md`

Sealed implementation diff evidence:

```text
git diff --name-only -- reference/python/nollm/dream_geometry/geometry reference/python/nollm/dream_geometry/field reference/python/nollm/dream_geometry/evidence reference/python/nollm/dream_geometry/cortex reference/python/nollm/dream_geometry/recall
```

Result: no paths.

## Validation

Commands run from repository root unless noted:

```text
python -m pytest -q reference/python/tests/test_di1_integration_shell_contract.py reference/python/tests/test_di1_integration_shell_public_view.py reference/python/tests/test_di1_integration_shell_read_only.py reference/python/tests/test_di1_integration_shell_boundaries.py reference/python/tests/test_di1_integration_shell_determinism.py
```

Result: `25 passed`.

```text
python -m pytest -q reference/python/tests/test_di1_integration_shell_contract.py reference/python/tests/test_di1_integration_shell_public_view.py reference/python/tests/test_di1_integration_shell_read_only.py reference/python/tests/test_di1_integration_shell_boundaries.py reference/python/tests/test_di1_integration_shell_determinism.py reference/python/tests/test_dr1_01_closure.py reference/python/tests/test_context_boundary.py reference/python/tests/test_package_hygiene_script.py
```

Result: `61 passed`.

```text
python -m pytest -q reference/python/tests/test_dg1_coverage_kernels.py reference/python/tests/test_dg1_chart_transforms.py reference/python/tests/test_dg2_field_boundaries.py reference/python/tests/test_dg2_trace_propagation.py reference/python/tests/test_de1_memory_substrate.py reference/python/tests/test_de1_boundaries.py reference/python/tests/test_dc1_cortex_compiler.py reference/python/tests/test_dr1_cross_module_contracts.py reference/python/tests/test_dg0_v2_dependency_firewall.py
```

Result: `100 passed`.

```text
python reference/python/nollm/dream_geometry/validation/di1_integration_shell_report.py
python reference/python/scripts/check_package_hygiene.py
git diff --check
```

Result: report regenerated; package hygiene passed; diff check passed.

```text
cd reference/python
python run_tests.py
```

Result: `1138 passed, 183 subtests passed`.

```text
cd reference/python
python -m nollm.cli validate ../../examples/openclaw
python -m nollm.cli audit ../../examples/openclaw
python -m nollm.cli audit-check ../../examples/openclaw --against ../../examples/audit_reports/openclaw_audit.json
```

Result: validate passed; audit passed with `issue_count: 0`; audit-check matched with `drift_count: 0`.

```text
cd reference/python
python -m nollm.cli tool ../../examples/tool_requests/audit_openclaw.json
python -m nollm.cli tool ../../examples/tool_requests/orient.json
python -m nollm.cli tool ../../examples/tool_requests/generated_output_examples/recall_scale_scan.json
```

Result: all returned `ok: true`. The generated recall example wrote
`examples/openclaw/recalls/recall_20260701_000001.{json,md}` during execution;
those generated artifacts were deleted and package hygiene was re-run.

## Baseline Report

Generated: `docs/validation/DI1_INTEGRATION_SHELL_BASELINE_REPORT.md`.

The report records:

- public operations;
- public response field allowlist;
- explicitly hidden internal field categories;
- synthetic fixture statuses;
- no-ledger-write evidence;
- deterministic mapping fingerprints;
- explicit non-goals.

## Bundle

The single-file Git bundle is created outside the repository after final commit.
Bundle path, `git bundle verify`, list-heads, and SHA-256 are recorded in the
final handoff.

## Boundary Confirmation

Confirmed:

- DI1 only supports `capabilities` and `recall`.
- DI1 does not compile Query or Growth objects.
- DI1 does not construct, scan, cache, or persist `RecallUniverse`.
- DI1 calls sealed DR1 through the public facade.
- DI1 materializes only DR1-selected DreamShard and explicit context records.
- Public output does not expose internal tie-break state, structure metrics,
  traversal identifiers, cell/chart/cover/trace/kernel identifiers, filesystem
  locations, store roots, Python exception types, or traceback text.
- Interpretation and Revision remain contextual and do not replace DreamShard
  evidence.
- Relative-time resolution is host-supplied; DI1 does not read the system clock
  or rewrite calendar spans.
- No network, CLI, OpenClaw, runtime, database, cache, session, write path,
  real memory hook, or global window admission was implemented.
