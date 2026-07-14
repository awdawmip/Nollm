# Nollm Current Status

Date: 2026-07-14

Accepted active baseline: `3528c0130a2f29987e06105753310d3b2a592a2a`.
Runtime-truth implementation checkpoint: `e2ac451ec39befc5cfd539f1260268126ec072f7`.

Current completed task:
`NOLLM_CAOLD_REAL_GEOMETRIC_CLUSTER_LOOP_TASK_20260714.md`.

V3.4 is the active core-function route. V3.3 remains the semantic-memory
architecture basis. OpenClaw channel delivery is
classified as `AFTER_DELIVERY`; CLI/webchat completion is classified as
`AFTER_TURN`. Hook callbacks capture bounded observations and return before
prompt construction, subagent execution, parsing, or Store access. Real user
material comes from `message_received.content` or user/assistant role messages
in `agent_end.messages`; Host and system prompts are excluded.

Inherited and dedicated model runs both preserve Host-owned model resolution.
The runtime records the actual provider/model from the child session rather
than accepting a configured `host-inherit` label as proof. Statement formation
remains `deliver=false`, has no main-agent tool, and uses no Python semantic
fallback.

The real revision checkpoint at
`a1a368d115f133b973011e5275fa15fb8f66b990` is the accepted input. CAOLD now
also validates Access-generated finite geometry candidates, real LLM
`candidate_id` selection, two separated multi-Cell clusters, per-anchor Core
Recall isolation, Gateway restart, fresh-session hidden Recall, and failure
rollback without cursor movement.

The user OpenClaw instance remains installed and enabled. Its StatementStore
and Nollm workspace were not cleared or reset. Plugin-disabled comparison and
dedicated-policy probes ran only in an independent temporary OpenClaw profile.

OpenClaw depends on Access rather than Core. `AccessMemoryLoop` owns pure
content-independent candidate generation, deterministic candidate mapping,
bounded Core/Statement/Handle/Recall composition, and rollback. OpenClaw owns
Host conversation, model calls, the bounded anchor/entry cursor, and hidden
injection. The active plugin is version `0.5.0` and uses placement wire contract
`nollm_openclaw_placement_v2`.

The installed plugin remains enabled and existing Nollm data remains intact.
This stage does not claim global semantic quality, large-scale geometry,
cross-cluster stitching, History completion, long-term stability, release
readiness, complete safety, or cross-provider portability.
