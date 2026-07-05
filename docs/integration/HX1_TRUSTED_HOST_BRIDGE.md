# HX1 Trusted Host Bridge

`nollm.dream_geometry.host_execution` exposes:

```python
execute_host_plan(plan, bindings, context)
preflight_host_plan(plan, bindings, context)
receipt_to_mapping(receipt)
error_to_mapping(error)
```

The bridge is intentionally host-controlled. Opaque CX2 refs are never resolved by scanning stores. The host supplies immutable bindings that pair declaration refs with actual CI1, BA1, DA1, DF1, DG6, DR1, and DI1 public API values.

The work-root may contain only lower-layer side effects from evidence, capture, cortex, and admission stores plus HX1 marker/receipt files. HX1 does not create field, assembly, recall, cache, database, or global-field directories.

Partial outcomes are explicit. If capture succeeds and admission later fails, the capture receipts and deferred candidates remain, the receipt status is `partial`, and no rollback is attempted.

For `mixed_explicit`, the bridge requires the actual same-call BA1/DA1 admission ids to exactly match the explicit assembly ids. A control record that is admitted but not assembled must be established by a prior host-controlled setup call, then omitted from the mixed plan.

Receipt reopen is bound by `execution_input_fingerprint`. The same owned work-root and same plan id are not enough to reuse a receipt when the plan, bindings, or execution context changed.
