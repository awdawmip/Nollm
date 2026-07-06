# HCG1 File-First Capture Gateway

HCG1 defines a local, file-first host capture gateway for Dream Geometry V2.

The gateway accepts only host-provided JSON files. It decodes those files into
CI1 public `CaptureRequest` and `CapturePolicy` values, mechanically projects a
capture-only CX2 `CortexActionPlan`, and executes that plan through the HX1
public `execute_host_plan` bridge.

HCG1 is limited to:

- host-explicit Capture;
- CI1/DE1 DreamShard persistence through existing public contracts;
- explicit physical visibility reads through `session_window`,
  `source_window`, and `persistent_explicit` selectors;
- stable JSON envelopes for success and rejection.

HCG1 does not implement Admission, PromotionDecision, GrowthProposal,
PlacementPlan, Geometry, FieldSnapshot, Assembly, QueryProbe, Recall, semantic
search, ranking, OpenClaw integration, runtime services, networking, databases,
or caches.

Capture success does not mean admission success. A deferred candidate is not an
admitted record. A visibility read is not recall.

## Capture Input

The capture command receives:

- `request_id`;
- `capture_request`;
- `capture_policy`.

Unknown fields, duplicate JSON object keys, malformed JSON, missing required
fields, ephemeral persistence, and `current_turn` visibility are rejected before
capture execution.

The workspace is never read from the JSON request. The CLI `--workspace` value
is the only work root input.

## Read Input

The read command receives:

- `request_id`;
- `selector`.

Allowed selectors are:

- `{"scope":"session_window","context_ref":"..."}`;
- `{"scope":"source_window","context_ref":"..."}`;
- `{"scope":"persistent_explicit","shard_ids":["..."]}`.

The gateway does not scan capture or evidence directories. It calls CI1
`CaptureVisibility` for the explicit selector supplied by the host.

## Workspace Contract

Capture uses HX1 owned work roots. Read requires a valid HX1 owned-root marker
and rejects arbitrary paths or isolated stores.

HCG1 removes HX1 scaffolding for stages not executed by the capture-only path,
leaving durable state only for the HX1 marker/receipt, CI1 capture state, and
DE1 evidence.
