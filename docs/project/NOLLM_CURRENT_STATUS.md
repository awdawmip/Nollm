# Nollm Current Status

Date: 2026-07-12

Accepted active baseline: `3528c0130a2f29987e06105753310d3b2a592a2a`.
Runtime-truth implementation checkpoint: `e2ac451ec39befc5cfd539f1260268126ec072f7`.

Current authorized task:
`NOLLM_AOLD_INVISIBLE_RUNTIME_TRUTH_REV1_TASK_20260712.md`.

V3.3 is the active semantic-memory route. OpenClaw channel delivery is
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

The user OpenClaw instance remains installed and enabled. Its StatementStore
and Nollm workspace were not cleared or reset. Plugin-disabled comparison and
dedicated-policy probes ran only in an independent temporary OpenClaw profile.

Core, Snapshot, Trace, Access, History, and Audit production implementations
are unchanged. This stage validates runtime lifecycle, evidence, model binding,
and interaction boundaries. It does not claim MemoryStatement semantic
accuracy, Placement, Recall, cross-provider portability, or long-term quality.
