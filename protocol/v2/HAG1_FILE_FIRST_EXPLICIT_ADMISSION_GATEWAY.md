# HAG1 File-First Explicit Admission Gateway

HAG1 adds one local trusted-host admission entry point:

```text
python reference/python/scripts/run_nollm_host_admission_gateway.py admit --workspace <hx1-owned-workspace> --request <json>
```

The gateway accepts only `nollm_hag_admission_request` version `1`. The request must name the real CI1 deferred candidate, the real DreamShard shard ID, promotion decision, growth submission, and placement plan explicitly. Workspace selection is only a CLI argument and is never accepted from JSON.

Public HAG identity is actual CI1/DE1 identity:

- `candidate_id` is the real CI1 candidate ID.
- `shard_id` is the real DreamShard ID, such as `shard:ci1:...`.
- Host-supplied `shard_...` or `shard_hag1_...` values are not public shard aliases and are rejected when they do not match the candidate.

HAG derives CX2-compatible `dac_...` and `shard_...` refs locally for the sealed CX2 plan. These refs are shown under `cx2_projection` in the response, but they are not DreamShard IDs, not candidate IDs, not persistent aliases, and not externally readable registry entries.

HAG1 v1 only accepts the window subset HX1 can represent without loss:

- exactly one `source_window_refs` entry;
- `opened_at == submitted_at`;
- `closed_at == null`;
- `status == ready_for_selection`.

Execution is mechanical:

1. Strict decode rejects malformed, duplicate-key, unknown-field, automation, path, raw-content, and non-promote request shapes before durable I/O.
2. The workspace must already contain the HX1 owned-root marker `{"owner":"hx1","marker_version":"1"}`.
3. HAG1 resolves the real CI1 deferred candidate through the public capture state store and checks candidate/shard identity before evidence lookup.
4. HAG1 reads the exact declared DreamShard through the public DE1 evidence store.
5. HAG1 projects a CX2 `intent=admission` plan and exact HX1 `HostAdmissionBinding` values that bridge internal projection refs to actual identities.
6. HAG1 calls only public `execute_host_plan(...)`.

HAG1 does not discover candidates, generate decisions, generate growth submissions, generate geometry or placement, assemble a field, recall, run OpenClaw, access network services, use databases, or register a V1 CLI/tool surface.
