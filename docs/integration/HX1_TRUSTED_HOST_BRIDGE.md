# HX1 Trusted Host Bridge

`nollm.dream_geometry.host_execution` exposes:

```python
execute_host_plan(plan, bindings, context)
preflight_host_plan(plan, bindings, context)
receipt_to_mapping(receipt)
error_to_mapping(error)
```

The bridge is intentionally host-controlled. Opaque CX2 refs are never resolved by scanning stores. The host supplies immutable bindings that pair declaration refs with actual CI1, BA1, DA1, DF1, DG6, DR1, and DI1 public API values.

Preflight is the only place where untrusted host objects are accepted. It validates CX2 plan shape before binding comparisons, then validates the canonical nested public values used by fingerprinting and staged calls. Bad plan declarations fail as `HX1_INVALID_PLAN`; malformed host public values fail as `HX1_INVALID_BINDINGS`; malformed context fields or DG6 enablement contradictions fail as `HX1_INVALID_CONTEXT`.

The work-root may contain only lower-layer side effects from evidence, capture, cortex, and admission stores plus HX1 marker/receipt files. It must be outside protected repository roots and their descendants. HX1 detects the source repository from the HX1 module path, not from the caller cwd, and also protects the caller cwd repository when one exists. Detection uses pathlib only; it does not call git, subprocess, shell, network, or environment discovery. HX1 does not create field, assembly, recall, cache, database, or global-field directories.

Partial outcomes are explicit. If capture succeeds and admission later fails, the capture receipts and deferred candidates remain, the receipt status is `partial`, and no rollback is attempted.

For `mixed_explicit`, the bridge requires the actual same-call BA1/DA1 admission ids to exactly match the explicit assembly ids. A control record that is admitted but not assembled must be established by a prior host-controlled setup call, then omitted from the mixed plan.

DG6 is verification-only. The bridge projects DG6 only when a DG6 derived view is declared, an exact DG6 verification binding is supplied, and `HostExecutionContext.enable_dg6_verification` is true. If no DG6 view is declared, the host may disable DG6 and receive a completed receipt with no projection id. If no DG6 view is declared but a DG6 binding is supplied, preflight rejects the input.

Receipt reopen is bound by `execution_input_fingerprint`. The same owned work-root and same plan id are not enough to reuse a receipt when the plan, bindings, canonical DreamShard payload, or execution context changed.
