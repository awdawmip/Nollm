# AOLD LLM-Native Evidence and Main-Agent Recall Report

Date: 2026-07-22

Status:

```text
AOLD_LLM_NATIVE_MAIN_AGENT_RECALL_IN_PROGRESS_AT_217f512559385a93fdd79b56b32f7894c6016293
```

This report records an implementation checkpoint. Provider and main-agent Live
gates were not executed, and the old deterministic target/NONE/leakage claims
are withdrawn below. No Provider result is fabricated.

## Delivery identity

- Input: `a4d8e3135ef894453e1d01dc5c19139d23d9c71f`
- Gate 0: `1f0a65b7601b488b9ffffe54f0391edbd79e3aae`
- Code/evidence: `217f512559385a93fdd79b56b32f7894c6016293`
- Final binding/docs: the commit containing this report
- Branch: `codex/aold-llm-native-evidence-main-agent-recall-selectivity`

The Core tree is unchanged. Both input and code/evidence commits resolve
`packages/nollm-core` to tree
`83bb1fb4d28a0ee2a2a3f3f3efc85f1b4ba7c0c7`.

## Writer and Evidence

The active Host parser accepts only
`nollm_openclaw_contextual_proposition_writer_v3`. Ordinary v1 and v2
responses fail with `invalid_writer_schema`; v1 conversion is available only
through the explicit offline migration function and is marked `coarse`.

Writer v3 emits exact quote refs and no `start`, `end`, or
`basis_span_indexes`. Access resolves exact Python codepoint spans without
normalization and covers Chinese, Japanese, English, emoji, newlines,
cross-role quotes, repeated quotes, occurrence/context disambiguation,
normalization mismatch, missing quotes, and long Captures.

This removes the deterministic offset/index failure class that contributed to
the Rev4 31-attempt baseline. New Provider first-attempt success was not
measured in this checkpoint.

Each new durable Statement receives an Access-owned canonical provenance
sidecar containing content digest, source/context Captures, exact spans,
resolved-reference cross-links, Writer schema/prompt, creation time, migration
precision, and optional revision predecessor. Reopen and idempotency pass.
Injected provenance write failure leaves no Statement, provenance, Handle, or
Core Atom.

## Cartography freshness

Every resolved Cartography plan now carries a canonical token binding Writer
propositions, plans, Core state, Atlas/page fingerprints, selected
region/entry data, existing Handles, and schema/prompt versions. Apply
recomputes and compares the field state before Admission. State changes and
token tampering fail before writes; this implementation conservatively rejects
even an unrelated far-Cell mutation.

## Main-agent Recall

The active plugin registers one internal `nollm_memory` tool. Its model-visible
parameters are limited to action, operation/region/entry IDs, and
`default|expanded` budget IDs. Query text, Statement lookup, q/r/layer,
Topic, vector, graph, and multi-entry parameters are absent.

Physical Cells and Handles remain in the plugin's bounded in-memory operation
state and are removed from tool results. The active
`agent_turn_prepare` path returns only Pending read-your-writes context.
`legacyReaderEnabled()` is false, so admitted Recall starts zero independent
Reader children. The old Reader code remains only as a Lab/A-B baseline.

Default Locality is one entry, geometry-ranked, at most four Statements and
3000 characters. One expansion returns a full larger window from the same
entry, at most eight Statements and 6000 characters. Mutation invalidates the
operation. No Python semantic filter or second model selection is used.

## Scale results

The Windows deterministic v7 workspace contains 80 Statements in eight
Localities, including 20 independent unrelated seeds and a ten-fact dense
Locality. The 57-case matrix includes 20 relevant, 10 relation-entry
target-hidden, 10 dense hidden-target, 10 NONE/unrelated, five same-entry
expand, and two cold restart cases.

| Metric | Result |
| --- | ---: |
| target reach | withdrawn: target selected from the result |
| expanded target reach | withdrawn: target selected from the result |
| cold restart reach | 100% |
| default result p95 | 4 |
| default characters p95 | 224 |
| maximum unrelated leakage | withdrawn: returned IDs were not checked |
| single-entry rate | 100% |
| hidden child calls | 0 |
| local tool p95 | 624.6 ms |

The fixed Rev4 hidden Reader observations were 19.7 to 33.7 seconds. The new
local tool measurement removes that extra Provider call, but it is not a live
same-query visible-answer A/B result.

## Evidence freeze

Code/evidence commit `217f512` contains:

| File | Git blob | Lines | Bytes | SHA-256 of blob bytes |
| --- | --- | ---: | ---: | --- |
| `validation/aold_llm_native_main_agent_recall_20260722.jsonl` | `29cbcdbc2ff08c95afe88ce3c9abe54db94952b7` | 59 | 26015 | `9271af16b40222c96bf7290a209ad1f04bed865892f6b023c89d266b21cba487` |
| `validation/aold_llm_native_main_agent_recall_summary_20260722.json` | `e30ced0e1dd7042275a35c59b4e8c60e65884459` | 1 | 929 | `96574f7fcb1838eec836c37862b4bda59f841e75896eea7a870e3678f845ca6b` |

Provider/model, raw Writer/Cartographer attempts, real NONE, and visible
main-answer quality have no events in this checkpoint. The frozen summary
records `provider_backed_statement_count=0` and `provider_gate_met=false`; its
stated prohibition reason is historical report text, not active authority.

## Verification

- Access + formation Python: 200 passed.
- Core + Snapshot + Trace: 98 passed.
- Rev3/Rev4/Rev5 evidence regressions: 8 passed.
- Rev5 Lab/counterexamples: 2 passed.
- OpenClaw Node SDK/plugin: 52 passed.
- Cartographer focused: 10 passed.
- Ownership: tracked equals rows, zero unclassified.
- Production boundaries: zero violations, zero cycles; migration baseline 7.
- Core tree unchanged from input.

## Actual vector and limits

```text
CORE 0% | SNAPSHOT 0% | TRACE 0% | ACCESS +15% |
HISTORY 0% | AUDIT 0% | OPENCLAW +15% |
LAB +15% | DISTRIBUTIONS +5%
```

Access and OpenClaw reach the Rev5 implementation checkpoint; Lab proves only
bounded function behavior after an entry is supplied. Remaining limitations are the
unrun 20-Statement Provider gate, unmeasured Writer first-attempt/final-durable
rates, unverified live install/diagnose behavior, and unobserved natural visible
main-agent answers. Multi-cell, multi-entry, Stitch, Topic/Entity,
vector/graph/embedding, Provider replacement, and Core changes remain outside
scope.
