# Nollm OpenClaw Memory Companion Skill

Use this skill only when the workspace has enabled the Nollm companion tools.
These tools supplement OpenClaw memory-core; they do not replace it.

Workflow:

1. Use `nollm_memory_search` when prior workspace, project, or user context could materially help the answer.
2. Treat `retrieval_score` as candidate relevance and `gravity_report` as orientation.
3. Use `nollm_memory_get` before making a factual user-facing claim from a recalled item.
4. Treat source path / provenance as mandatory context for factual use.
5. Interpret drift:
   - `core` / `halo`: close to entry frame.
   - `near_drift`: relevant lateral context; inspect source.
   - `far_coherent`: explore only when it adds useful perspective.
   - `far_weak` / `semantic_break` / `unglued`: caution; do not treat as authoritative.
6. Use `nollm_memory_write_candidate` only when the user explicitly asks to remember/save something or a memory-worthy event is explicitly confirmed by policy.
7. Never claim that a pending candidate has been written to `MEMORY.md`.

Gravity report = instrumentation, not permission.
Drift class = orientation, not trust.

Do not treat `drift_class` as trust, status, a ranking permission, or a hard
rejection rule. Do not claim durable writes unless OpenClaw memory-core or the
operator performs them outside this companion tool.
