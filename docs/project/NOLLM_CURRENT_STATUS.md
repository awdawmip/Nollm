# Nollm Current Status

Date: 2026-07-13

Accepted active baseline: `3528c0130a2f29987e06105753310d3b2a592a2a`.
Runtime-truth implementation checkpoint: `e2ac451ec39befc5cfd539f1260268126ec072f7`.

Current authorized task:
`NOLLM_CAOLD_CROSS_SESSION_MEMORY_LOOP_REV1_TASK_20260713.md`.

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

Formation JSON resilience selected P1 in its historical matrix. The current
CAOLD loop is `IN_PROGRESS`: the bridge has restricted non-semantic repairs,
same-model retry only for JSON/schema failures, and a Windows UTF-8 transport
fix. Real Placement/Core writes and bounded Cursor persistence are recorded,
but new-session Recall injection and natural main-agent use remain unverified.

The user OpenClaw instance remains installed and enabled. Its StatementStore
and Nollm workspace were not cleared or reset. Plugin-disabled comparison and
dedicated-policy probes ran only in an independent temporary OpenClaw profile.

Core, Snapshot, Trace, Access, History, and Audit production implementations
are unchanged. This stage validates runtime lifecycle, evidence, model binding,
and interaction boundaries. It does not claim MemoryStatement semantic
accuracy, Placement, Recall, cross-provider portability, or long-term quality.
