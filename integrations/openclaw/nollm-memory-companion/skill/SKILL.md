# Nollm OpenClaw Memory Companion Skill

Use this skill only when the workspace has enabled the Nollm companion tools.
These tools supplement OpenClaw memory-core; they do not replace it.

Workflow:

1. Use `nollm_memory_recall` once when prior workspace, project, or user context could materially help the answer.
2. Treat `direct_evidence` as the factual recall path and `lateral_context` as optional orientation.
3. Use `memory_get` or `nollm_memory_get` before making a factual user-facing claim from a recalled item.
4. Treat source path / provenance as mandatory context for factual use.
5. Interpret drift:
   - `core` / `halo`: close to entry frame.
   - `near_drift`: relevant lateral context; inspect source.
   - `far_coherent`: explore only when it adds useful perspective.
   - `far_weak` / `semantic_break` / `unglued`: caution; do not treat as authoritative.
6. Use `nollm_memory_write_candidate` when the user asks to remember/save something. This stages only a pending candidate.
7. Use `nollm_memory_commit_candidate` only after the user explicitly confirms durable or daily commit, with `explicit_confirmation=true`.
8. Never claim that a pending candidate has been written to `MEMORY.md`.

Gravity report = instrumentation, not permission.
Drift class = orientation, not trust.

Do not treat `drift_class` as trust, status, a ranking permission, or a hard
rejection rule. Do not claim durable writes unless OpenClaw memory-core or the
explicit Nollm commit tool reports the exact file path, line range, and hashes.
