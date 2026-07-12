# Nollm OpenClaw Charter

Purpose: typed hooks, invisible background Dream agents, queues, session mapping, statement formation, placement workflow, recall injection, install/update/logging diagnostics.

- Persistent state: adapter configuration and host correlation state; no Core facts.
- Temporary state: bounded conversation material, hook queues, Dream run correlation, bounded placement requests, recall context.
- Public API: native OpenClaw hooks/subagent runtime and Access public API. Default Formation is post-delivery, `deliver=false`, and absent from the main agent tool table.
- Forbidden API: Core private access, memory-provider ownership, direct provider HTTP, Python semantic placement.
- Dependencies: Access; host OpenClaw SDK. It does not depend on Core private modules.
- Failure: adapter actions may defer; Core correctness remains unchanged.
- Distributions: `nollm-openclaw`, debug, audited.
- Future repository: `nollm-openclaw`.
- Current sources: `integrations/openclaw/**` and associated host documentation/scripts.
