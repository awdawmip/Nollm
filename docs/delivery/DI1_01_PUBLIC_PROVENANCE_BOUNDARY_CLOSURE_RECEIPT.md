# DI1.1 Delivery Receipt - Public Provenance Boundary Closure

## Scope

Task pack:
`NOLLM_DI1_AUDIT_AND_DI1_01_PUBLIC_PROVENANCE_BOUNDARY_CLOSURE_TASK_PACK_20260701.md`.

DI1.1 closes only the public provenance boundary in the DI1 Public Recall
Envelope. Raw DE1 free-text provenance fields are no longer emitted:

- `OriginDescriptor.reference`
- `OriginDescriptor.context_reference`
- `OriginDescriptor.role_label`
- `TemporalContext.source_time_expression`
- `TemporalContext.locale_hint`

They are projected as deterministic `absent` / `present_redacted` state fields.
DreamShard content, selected Interpretation statements, Revision relations,
status, tier, matched axes, and fixed selection basis remain unchanged.

## Baseline

- Start branch: `feature/di1-integration-shell-foundation`
- DI1.1 branch: `feature/di1-01-public-provenance-boundary-closure`
- Required DI1 baseline commit: `51a39a5a6d699f50c5a273a851557f4dc60162a9`
- Required sealed commits confirmed present:
  - DG1: `314f0d93ce04977588db933969ea71c216351a7b`
  - DG2: `74b00a93b93abd22aadf08988a9d5947992f6e22`
  - DE1: `c2a28c25cb472a8911c8bd8367a27351c6606aec`
  - DC1: `19d516681301ee9213b7591fd36f9775ebb5207e`
  - DR1: `bfda03bdd458fd5a9cb057b9f8550e52fa3716c6`

Final HEAD, push status, bundle path, bundle SHA-256, and `git bundle verify`
are recorded in the final handoff after commit creation.

## Changed Paths

- `reference/python/nollm/dream_geometry/adapters/public_recall_view.py`
- `reference/python/tests/test_di1_integration_shell_public_view.py`
- `reference/python/tests/test_di1_integration_shell_determinism.py`
- `reference/python/nollm/dream_geometry/validation/di1_integration_shell_report.py`
- `docs/validation/DI1_INTEGRATION_SHELL_BASELINE_REPORT.md`
- `protocol/v2/DI1_INTEGRATION_SHELL_CONTRACT.md`
- `protocol/v2/INVARIANTS.md`
- `docs/delivery/DI1_01_PUBLIC_PROVENANCE_BOUNDARY_CLOSURE_RECEIPT.md`
- `docs/delivery/DI1_DELIVERY_RECEIPT_20260701.md` whitespace-only EOF cleanup for required diff check.

Sealed implementation paths under Geometry, Field, Evidence, Cortex, and Recall
were not modified.

## Validation

Commands run:

```text
python -m pytest -q reference/python/tests/test_di1_integration_shell_contract.py reference/python/tests/test_di1_integration_shell_public_view.py reference/python/tests/test_di1_integration_shell_read_only.py reference/python/tests/test_di1_integration_shell_boundaries.py reference/python/tests/test_di1_integration_shell_determinism.py reference/python/tests/test_dr1_01_closure.py reference/python/tests/test_context_boundary.py reference/python/tests/test_package_hygiene_script.py
```

Result: `65 passed`.

```text
python -m pytest -q reference/python/tests/test_dg1_coverage_kernels.py reference/python/tests/test_dg1_chart_transforms.py reference/python/tests/test_dg2_field_boundaries.py reference/python/tests/test_dg2_trace_propagation.py reference/python/tests/test_de1_memory_substrate.py reference/python/tests/test_de1_boundaries.py reference/python/tests/test_dc1_cortex_compiler.py reference/python/tests/test_dr1_cross_module_contracts.py reference/python/tests/test_dg0_v2_dependency_firewall.py
```

Result: `100 passed`.

```text
python reference/python/nollm/dream_geometry/validation/di1_integration_shell_report.py
python reference/python/scripts/check_package_hygiene.py
git diff --check HEAD^
```

Result: report regenerated; package hygiene passed; diff check passed after
removing one pre-existing trailing blank line from the DI1 receipt.

```text
cd reference/python
python run_tests.py
```

Result: `1142 passed, 183 subtests passed`.

```text
cd reference/python
python -m nollm.cli validate ../../examples/openclaw
python -m nollm.cli audit ../../examples/openclaw
python -m nollm.cli audit-check ../../examples/openclaw --against ../../examples/audit_reports/openclaw_audit.json
```

Result: validate passed; audit passed with `issue_count: 0`; audit-check
matched with `drift_count: 0`.

```text
cd reference/python
python -m nollm.cli tool ../../examples/tool_requests/audit_openclaw.json
python -m nollm.cli tool ../../examples/tool_requests/orient.json
python -m nollm.cli tool ../../examples/tool_requests/generated_output_examples/recall_scale_scan.json
```

Result: all returned `ok: true`. The recall example generated
`examples/openclaw/recalls/recall_20260701_000001.{json,md}` and those generated
artifacts were removed before final package hygiene and audit-check.

## Boundary Confirmation

Confirmed:

- Origin free-text provenance is never emitted raw.
- Temporal free-text provenance is never emitted raw.
- Origin kind and DE1-validated RFC3339 instants remain public.
- DreamShard content and selected Interpretation statements are not scanned,
  rewritten, summarized, or redacted.
- DR1 status, tier, and selection are not reordered or reinterpreted by DI1.
- No write path, cache, session, network, runtime, OpenClaw, CLI, database,
  security sandbox, permission model, source truth classification, privacy
  ontology, string classifier, or semantic logic was added.
