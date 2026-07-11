# Nollm OpenClaw Charter

Purpose: typed hooks, tools, skills, queues, session mapping, statement formation, placement workflow, recall injection, install/update/logging diagnostics.

- Persistent state: adapter configuration and host correlation state; no Core facts.
- Temporary state: hook queues, bounded placement requests, recall context.
- Public API: native OpenClaw tools/hooks and Access public API.
- Forbidden API: Core private access, memory-provider ownership, direct provider HTTP, Python semantic placement.
- Dependencies: Access; host OpenClaw SDK. It does not depend on Core private modules.
- Failure: adapter actions may defer; Core correctness remains unchanged.
- Distributions: `nollm-openclaw`, debug, audited.
- Future repository: `nollm-openclaw`.
- Current sources: `integrations/openclaw/**` and associated host documentation/scripts.
