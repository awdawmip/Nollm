# Nollm Current Status

Date: 2026-07-22

```text
route: NOLLM_ROUTE_BOOK_V3_9_FAST_STRUCTURAL_GEOMETRY_20260715.md
task: NOLLM_A_O_L_D_LLM_NATIVE_EVIDENCE_STALE_PLAN_MAIN_AGENT_RECALL_SELECTIVITY_TASK_20260722.md
status: AOLD_LLM_NATIVE_MAIN_AGENT_RECALL_IN_PROGRESS_AT_217f512559385a93fdd79b56b32f7894c6016293
input HEAD: a4d8e3135ef894453e1d01dc5c19139d23d9c71f
code/evidence HEAD: 217f512559385a93fdd79b56b32f7894c6016293
evidence: validation/aold_llm_native_main_agent_recall_20260722.jsonl
summary: validation/aold_llm_native_main_agent_recall_summary_20260722.json
```

Active truth:

- Writer v3 is the only active Host schema; v1 migration is explicit/offline and v2 has no active fallback.
- LLM output contains quote refs, while Access deterministically computes exact codepoint spans and canonical digests.
- New durable Statements have reopenable Access-owned provenance; resolved-reference basis IDs cross-link exact Evidence refs.
- Cartography plans bind Writer, field, Atlas/page, selected entries, Handles, and schema/prompt identity. Stale apply is zero-write.
- The main agent owns one internal `nollm_memory` tool call path. Model-visible parameters contain no coordinates or query/Statement lookup.
- Default Locality is one entry and at most 4 Statements/3000 characters; one same-entry expansion allows 8/6000.
- The 80-Statement, eight-Locality, 57-query deterministic matrix achieved 100% target/expanded/restart reach, p95 4 Statements/224 characters, zero unrelated leakage, and zero hidden child calls.
- The Provider-backed 20-Statement gate, Writer first-attempt rate, and natural visible-answer quality were not run because live OpenClaw/model calls are prohibited. Status therefore remains IN_PROGRESS.
- Core tree `83bb1fb4d28a0ee2a2a3f3f3efc85f1b4ba7c0c7` is unchanged from input.

Task vector:

```text
CORE 0% | SNAPSHOT 0% | TRACE 0% | ACCESS +15% |
HISTORY 0% | AUDIT 0% | OPENCLAW +15% |
LAB +15% | DISTRIBUTIONS +5%
```
