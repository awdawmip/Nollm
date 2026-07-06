# HAG1 File-First Explicit Admission Gateway

HAG1 adds one local trusted-host admission entry point:

```text
python reference/python/scripts/run_nollm_host_admission_gateway.py admit --workspace <hx1-owned-workspace> --request <json>
```

The gateway accepts only `nollm_hag_admission_request` version `1`. The request must name the deferred candidate, promotion decision, growth submission, and placement plan explicitly. Workspace selection is only a CLI argument and is never accepted from JSON.

Execution is mechanical:

1. Strict decode rejects malformed, duplicate-key, unknown-field, automation, path, raw-content, and non-promote request shapes before durable I/O.
2. The workspace must already contain the HX1 owned-root marker `{"owner":"hx1","marker_version":"1"}`.
3. HAG1 resolves the real CI1 deferred candidate through the public capture state store and reads the DreamShard through the public DE1 evidence store.
4. HAG1 projects a CX2 `intent=admission` plan and exact HX1 `HostAdmissionBinding` values.
5. HAG1 calls only public `execute_host_plan(...)`.

HAG1 does not discover candidates, generate decisions, generate growth submissions, generate geometry or placement, assemble a field, recall, run OpenClaw, access network services, use databases, or register a V1 CLI/tool surface.
