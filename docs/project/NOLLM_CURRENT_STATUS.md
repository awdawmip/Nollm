# Nollm Current Status

Date: 2026-07-14

Accepted active baseline: `3528c0130a2f29987e06105753310d3b2a592a2a`.
Runtime-truth implementation checkpoint: `e2ac451ec39befc5cfd539f1260268126ec072f7`.

Current completed task:
`NOLLM_CAOLD_REAL_REVISION_LOOP_TASK_20260713.md`.

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

The cross-session checkpoint at
`c3354743482e50477052c5095b0b8a30e1bbd1ee` is validated. The project has
entered the "works correctly" stage. CAOLD now validates natural correction,
real LLM `revision_current`, Access-owned atomic revision, duplicate reuse,
similar-distinct creation, restart, and current-only cross-session Recall.

The user OpenClaw instance remains installed and enabled. Its StatementStore
and Nollm workspace were not cleared or reset. Plugin-disabled comparison and
dedicated-policy probes ran only in an independent temporary OpenClaw profile.

OpenClaw now depends on Access rather than Core. `AccessMemoryLoop` owns the
bounded Core/Statement/Handle/Recall composition, while OpenClaw owns Host
conversation, model calls, cursor policy, and hidden injection. Production
boundary validation reports zero violations and zero cycles.

The installed plugin remains enabled and existing Nollm data remains intact.
This stage does not claim all memory quality, History completion, long-term
stability, release readiness, complete safety, or cross-provider portability.
