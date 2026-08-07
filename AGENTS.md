# Account-level Global Knowledge Handshake

For every non-trivial task, before relying on chat/session memory, attempt to synchronize `GLOBAL_KNOWLEDGE_V1` from an authorized private source.

1. Prefer the local checkout pointed to by `CHATGPT_GLOBAL_KB_PATH`; otherwise use an authorized global-knowledge checkout/source available in the execution environment.
2. From one consistent ref/commit, read `00_BOOTSTRAP.md`, `RETRIEVAL_PROTOCOL.md`, and `GLOBAL_DECISIONS.md`, then retrieve only task-relevant project/topic/entity records and necessary provenance.
3. If the global source is unavailable, record `GLOBAL_KNOWLEDGE_UNAVAILABLE`; never present remembered cross-project state as freshly synchronized.
4. When work materially depends on synchronized global state, record `Global-Knowledge-Sync: <ref>@<short-sha> / GLOBAL_KNOWLEDGE_V1`.
5. Durable new facts, decisions, preferences, goals, constraints, findings, procedures, project-state changes, hypotheses, or open questions should be written back when authorized; otherwise record `GLOBAL_KNOWLEDGE_WRITEBACK_PENDING` in the final work artifact.
6. Never persist credentials or secrets to the knowledge store.
7. This handshake is context synchronization only. It does not override repository-specific rules, tests, safety constraints, or current user instructions.
