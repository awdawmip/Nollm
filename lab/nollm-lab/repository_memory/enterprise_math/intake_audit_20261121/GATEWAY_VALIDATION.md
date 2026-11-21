# Gateway candidate verification — 2026-11-21

Base: Sites v23 source `e9dc770e03f39132d8a3dd4ab5d5cd7be4f91d56`.
This isolated candidate was not deployed. The existing hosted checkout was unchanged.

## Contract and relay tests

Command: `node --test tests/research-memory-gateway.test.mjs tests/catalog-compatibility.test.mjs`

Observed: **16 passed, 0 failed, 0 skipped**, 279.278827 ms.

The candidate SDK memory descriptors were generated from the actual Python MCP SDK 1.30.0. Tests compare all eight memory tools' parameter types, defaults, enum and numeric bounds, and read/write annotations. They also verify forwarding, unchanged existing read/write permissions, and the original link ID retained after an unknown stitch/unstitch outcome without replaying the write.

## Actual JavaScript gateway to Python MCP integration

Command (from this candidate checkout):

```sh
EM_LOCAL_BACKEND_ROOT=/workspace/scratch/4eeff3663e39/nollm_intake_audit_20261121/architecture/backend-candidate \
EM_LOCAL_TEST_PYTHON=/workspace/scratch/4eeff3663e39/nollm_mcp_20261120/test-venv/bin/python \
EM_LOCAL_NOLLM_RUNTIME=/workspace/scratch/4eeff3663e39/nollm_intake_audit_20261121/architecture/runtime-candidate/scripts/runtime \
node --test tests/integration/research-memory-real-backend.test.mjs
```

Observed: **1 passed, 0 failed, 0 skipped**, test body 49,114.483842 ms, total 49,363.742107 ms.

Each backend call starts a fresh Python process and opens the same temporary field. The gateway, MCP parameter handling, Python memory adapter, Nollm files, revision and Source line-window selection are real. External GitHub content is supplied by fixed-commit fixtures; no production field or research-role state is used. Existing scopes are exercised rather than replaced.

Covered behavior: save/read/revise and history; exact fixed sources; current_scope/source_freshness semantics; single native entry; directed connection creation and readback by original ID; target-cell peers appearing through a bridge; target revision read as current; bridge withdrawal; empty lookup after withdrawal; complete connected recall restored after withdrawal; no control worker started.

This is local integration evidence. The live v23 tests and independent reader traces are recorded separately in `online/` and `readers/`.
