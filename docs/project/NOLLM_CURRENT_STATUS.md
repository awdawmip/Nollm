# Nollm Current Status

Date: 2026-07-22

```text
route: NOLLM_ROUTE_BOOK_V3_9_FAST_STRUCTURAL_GEOMETRY_20260715.md
task: NOLLM_A_O_L_D_MAIN_AGENT_TOOL_SCOPE_PROVIDER_LIVE_SEMANTIC_SELECTIVITY_CLOSURE_TASK_20260722.md
status: AOLD_MAIN_AGENT_PROVIDER_LIVE_IN_PROGRESS_AT_9cc0f005cce15e022884ce4a0fb930b17668fe08
input HEAD: ec83e0cb22299f2d62d0d6e021911595f8c783a9
implementation checkpoint: 9cc0f005cce15e022884ce4a0fb930b17668fe08
evidence: validation/aold_main_agent_provider_live_selectivity_20260722.jsonl
summary: validation/aold_main_agent_provider_live_selectivity_summary_20260722.json
```

Active truth:

- Writer v3 is the only active Host schema; v1 migration is explicit/offline and v2 has no active fallback.
- LLM output contains quote refs, while Access deterministically computes exact codepoint spans and canonical digests.
- New durable Statements have reopenable Access-owned provenance; resolved-reference basis IDs cross-link exact Evidence refs.
- Cartography plans bind Writer, field, Atlas/page, selected entries, Handles, and schema/prompt identity. Stale apply is zero-write.
- The Host issues a bounded `nollm_memory` operation and binds it to trusted tool-call, session, run, workspace, Core, Atlas/page, Policy, region, and entry identity.
- Successful Recall suppresses Capture only for the exact run; later runs remain eligible. Cross-run Recall and stale or mismatched reopen are rejected.
- Default Locality is one entry and at most 4 Statements/3000 characters; one same-entry expansion allows 8/6000.
- The replacement 80-Statement fixture declares 47 targets before Recall and records `1.0` default/expanded/restart reach with zero forbidden-ID leakage.
- Semantic NONE and query-to-visible evidence remain unavailable because Provider/Host execution was not performed. Function timing is not reported as tool latency.
- `shadow-observation` and `active-memory` are explicit profiles; live install validation was not performed.
- Core tree `83bb1fb4d28a0ee2a2a3f3f3efc85f1b4ba7c0c7` is unchanged from input.

Task vector:

```text
CORE 0% | SNAPSHOT 0% | TRACE 0% | ACCESS 0% |
HISTORY 0% | AUDIT 0% | OPENCLAW +15% |
LAB +10% | DISTRIBUTIONS +5%
```
