# Nollm OpenClaw Charter

Purpose: typed hooks, invisible background Dream agents, queues, session mapping, statement formation, placement workflow, recall injection, install/update/logging diagnostics.

- Persistent state: adapter configuration and host correlation state; no Core facts.
- Temporary state: bounded conversation material, hook queues, Dream run correlation, bounded placement requests, recall context.
- Public API: native OpenClaw hooks/subagent runtime and Access public API. Channel `message_sent` is `AFTER_DELIVERY`; CLI/webchat `agent_end` is `AFTER_TURN`. Default Formation is `deliver=false` and absent from the main agent tool table.
- Forbidden API: Core private access, memory-provider ownership, direct provider HTTP, Python semantic placement.
- Dependencies: Access; host OpenClaw SDK. It does not depend on Core private modules.
- Failure: adapter actions may defer; Core correctness remains unchanged.
- Distributions: `nollm-openclaw`, debug, audited.
- Future repository: `nollm-openclaw`.
- Current sources: `integrations/openclaw/**` and associated host documentation/scripts.
- Runtime rule: Hook callbacks only capture bounded observations and schedule background work; prompt construction, subagent execution, parsing, and Store writes never run inline in the callback.
- Conversation material comes from `message_received.content` or real user/assistant role messages in `agent_end.messages`; Host and system prompts are excluded.
