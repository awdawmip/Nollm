# AOLD Invisible Runtime Truth Report

Date: 2026-07-12

## Scope And Baseline

The input implementation checkpoint is
`e2ac451ec39befc5cfd539f1260268126ec072f7`; it is not the active baseline.
The accepted active baseline is
`3528c0130a2f29987e06105753310d3b2a592a2a`.

Actual vector:

```text
CORE 0% | SNAPSHOT 0% | TRACE 0% | ACCESS 0% |
HISTORY 0% | AUDIT 0% | OPENCLAW +10% | LAB +5% | DISTRIBUTIONS +5%
```

Core, Snapshot, Trace, Access, History, and Audit production implementations
did not change.

## Runtime Contract

- `message_sent` is `AFTER_DELIVERY`; CLI/webchat `agent_end` is `AFTER_TURN`.
- Hook callbacks only capture bounded observations and schedule background work.
- An `AsyncResource` created at plugin registration keeps background subagent
  work outside the Host request authorization scope while preserving plugin
  identity.
- ConversationMaterial comes from `message_received.content` or real
  user/assistant messages in `agent_end.messages`. System and Host prompts are
  excluded, and stable TurnKey identities suppress duplicate Dream starts.
- The child session provides actual resolved provider/model evidence.
  Inherit and dedicated probes both resolved `meituan/LongCat-2.0`.
- Dedicated execution used an exact Host override allowlist. A preflight run
  proved request-scoped override rejection; the final background-scope run
  was authorized and completed with `deliver=false`.

## Controlled Live Evidence

The plugin-enabled group ran 15 ordinary CLI/webchat turns in five three-turn
sessions on the user's active OpenClaw 2026.6.11 instance. The disabled group
ran the same 15 prompts in an independent temporary profile, port, workspace,
state database, and session set. The active instance was never disabled or
uninstalled.

| Mode | Samples | Main success | One visible main reply | Median | p95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| enabled | 15 | 15 | 15 | 25,815 ms | 46,522.8 ms |
| disabled | 15 | 15 | 15 | 24,274 ms | 31,984.9 ms |

All 15 enabled Dreams reached a terminal state after their corresponding main
command returned. Hook callback p95 and maximum were both 0 ms. Dream-visible
messages and Python semantic fallbacks were both zero. Four model outputs were
invalid JSON/schema and failed open; this stage does not evaluate semantic
quality. The target environment exposed no controlled external channel target,
so five `message_sent` channel cases were not run. CLI/webchat `AFTER_TURN`
coverage exceeds the required five cases.

The enabled prompts were general questions and correctly produced no durable
StatementStore writes. Statement idempotency is therefore established by the
real `FileStatementStore` focused test: repeated stable
`TurnKey + prompt/schema + draft_id` output retains one canonical file, while
changed content at the same identity raises `FileExistsError` and cannot
overwrite the prior statement.

## Verifier

`verify_runtime_truth.py --check` reads raw Host JSON, raw visible payloads,
receipts, Hook events, Dream starts/terminals, and actual child model fields.
It does not call a model or trust receipt visible counts, summary counters,
`host-inherit` labels, or hand-authored verified flags. Mutation tests reject
phase changes, missing/extra replies, duplicate Dreams, model tampering,
pre-return completion claims, summary mismatch, system material, and duplicate
user turns.

## Regression Evidence

- Core: 39 passed; Snapshot: 7 passed; Trace: 3 passed; Access: 55 passed.
- OpenClaw Python adapter and runtime verifier: 30 passed.
- OpenClaw Node plugin: 11 passed; plugin import check passed.
- M0: 45 passed; governance/hygiene: 8 passed.
- Geometry parity: 9/9; Core capability: 25/25; minimal M1 E2E passed.
- Ownership manifest and module boundary verification report zero production
  violations and zero production cycles after regeneration.

## Preserved State And Limits

The user instance remains installed and enabled in inherit/statement-store
mode with diagnostic tracing disabled. Transcript persistence remains false.
The existing StatementStore and Nollm workspace were not cleared, reset, or
replaced. Destructive disabled and dedicated-policy work was confined to the
temporary profile. Manual continuation instructions are in
`docs/integration/openclaw/AOLD_RUNTIME_TRUTH_MANUAL_CHAT_HANDOFF.md`.

This evidence validates runtime lifecycle, model binding, bounded material,
nonblocking behavior, and Store identity boundaries. It does not validate
MemoryStatement semantic accuracy, Placement, Recall, other providers,
external channel delivery, cross-platform portability, or long-term quality.
