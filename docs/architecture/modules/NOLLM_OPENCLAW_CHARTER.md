# Nollm OpenClaw Charter

Purpose: typed hooks, durable visible-turn Capture, recoverable absorption workers, invisible background Dream agents, statement formation, placement workflow, pending/admitted recall injection, install/update/logging diagnostics.

- Persistent state: adapter configuration, immutable raw Capture files, append-only Capture state events, and bounded worker claims; no Core facts.
- Temporary state: bounded conversation material, hook queues, Dream run correlation, bounded placement requests, recall context.
- Temporary state includes at most one provisional revision confirmation and one exact-target blacklist for the current Placement operation; neither is persistent.
- Public API: native OpenClaw hooks/subagent runtime and Access public API. Channel `message_sent` is `AFTER_DELIVERY`; CLI/webchat `agent_end` is `AFTER_TURN`. Default Formation is `deliver=false` and absent from the main agent tool table.
- Forbidden API: Core private access, memory-provider ownership, direct provider HTTP, Python semantic placement.
- Dependencies: Access; host OpenClaw SDK. It does not depend on Core private modules.
- Failure: adapter actions may defer; Core correctness remains unchanged.
- Revision confirmation reject, invalid output, and timeout are zero-write outcomes. Only a confirmed same-subject, same-slot supersession may reach Access atomic apply.
- Distributions: `nollm-openclaw`, debug, audited.
- Future repository: `nollm-openclaw`.
- Current sources: `integrations/openclaw/**` and associated host documentation/scripts.
- Runtime rule: delivery Hooks may await only the local atomic Capture publish. Prompt construction, Provider calls, Python bridge, Surface/Core work, and Admission never run in the foreground Capture path.
- Conversation material comes from `message_received.content` or real user/assistant role messages in `agent_end.messages`; Host and system prompts are excluded.
- Capture identity is deterministic for one scope, turn identity, and exact user/assistant bytes. Duplicate Hooks replay the same immutable file.
- Pending fallback scans only bounded scope/time/count/character windows and never owns a semantic or relation index.
- One spool has one active worker. Processing claims expire and are recovered from immutable Capture plus state events after restart.
