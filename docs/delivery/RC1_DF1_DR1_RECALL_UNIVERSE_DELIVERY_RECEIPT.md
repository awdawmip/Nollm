# RC1 DF1 to DR1 RecallUniverse Delivery Receipt

Status: RC1-C1 implemented; waiting for independent acceptance. RC1 does not
complete DX2.

Original RC1 root baseline:

```text
1def9e0d4d2b0deb2ab2ad9db74f6d01d4a3dbf7
```

RC1-C1 input baseline:

```text
30c0c06782d47d324406800f68e21ea7aa58deb3
```

RC1 implementation commit:

```text
561e8b9c6b15bf47ceda7fbc864ab95fc2f3f4ec
```

RC1-C1 implementation commit:

```text
fbe44575c7e1d4d87e3b7c221655f74e2a57de64
```

Bundle filename:

```text
nollm_rc1_c1_support_trace_binding_closure_20260703.bundle
```

The bundle SHA-256 is recorded in the final delivery response because committing
the bundle hash inside this receipt would change the bundle identity.

Scope completed:

- Updated only `reference/python/nollm/dream_geometry/assembly/builder.py` as
  production code.
- Kept `FiniteFieldSnapshot.coarse_covers` as the DG2 local `CellRef` view.
- Bound `RecallUniverse.covers` to replayed `HexCell` values for DR1 execution.
- Closed RC1-C1 support binding: every declared support trace id must exist,
  and every support trace cell must match the cover identity. A matching subset
  cannot be used as a substitute for the full support set.
- Preserved raw local covers for DG2 gravity calculation.
- Added RC1 tests for single admission, view separation, multi-admission
  determinism, public reconstruction, missing support trace fail-closed, and
  partial identity mismatch fail-closed.
- Added RC1 validation runner and baseline report.

Validation completed:

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=reference/python python -m pytest -q ...` fixed RC1-C1 acceptance set:
  passed locally.
- `PYTHONDONTWRITEBYTECODE=1 python validation/rc1/run_df1_dr1_recall_universe_contract.py --output docs/validation/RC1_DF1_DR1_RECALL_UNIVERSE_CONTRACT_REPORT.md`:
  passed and reports `rc1_05_fail_closed_binding: pass`.
- `PYTHONDONTWRITEBYTECODE=1 python reference/python/scripts/check_package_hygiene.py`:
  passed locally.
- `git diff --check 30c0c06782d47d324406800f68e21ea7aa58deb3..HEAD`:
  passed locally.

Allowed-path diff:

- Production diff is limited to
  `reference/python/nollm/dream_geometry/assembly/builder.py`.
- Validation and documentation diff is limited to RC1-C1 allowed test, runner,
  report, scope, protocol, delivery receipt, and roadmap files.

Sealed-path diff:

- capture, evidence, cortex, admission, geometry, field, recall, adapters, and
  batch_admission production paths remain empty from RC1-C1 input baseline to
  delivery HEAD.

Public DF1-to-DR1 reproduction:

- Real DA1/DF1 fixture admission assembled through `assemble_field_snapshot(...)`
  resolves through DR1 with status `resolved` for the Kunming/rain probe.

Boundary:

- No field, recall, geometry, admission, evidence, cortex, capture, adapters,
  or batch admission production implementation was modified.
- No DX2 fixture, DX2 validation, DX2 delivery, runtime, OpenClaw, database,
  cache, network, LLM/NLP, embedding, global discovery, or persistent Field was
  added.

Known limitations:

- DX2 remains paused and incomplete.
- RC1-C1 only closes full support-trace binding for the DF1-to-DR1
  RecallUniverse executable cover contract.
