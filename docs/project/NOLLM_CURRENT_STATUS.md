# Nollm Current Status

Date: 2026-07-12

Input baseline: `bac2c7f06017f90adbc24ae3b71a99cae1581e85`.

Current authorized task: `NOLLM_AOLD_INVISIBLE_DREAM_AGENT_TASK_20260712.md`.

Status: V3.3 is the active semantic-memory route. Ordinary OpenClaw chat can
schedule bounded Dream Formation after the main reply through an invisible,
`deliver=false` background subagent. The default inherits the Host model and
credentials, stores no transcript, exposes no Formation tool, and writes only
to shadow mode. Explicit `statement-store` mode writes through the Access
`FileStatementStore` contract.

The three-round live gate used 45 ordinary chats on OpenClaw 2026.6.11. All 45
main chats returned successfully and started a Dream run after delivery. The
rounds completed 12, 12, and 11 structurally valid formations; model output
produced the remaining JSON/schema failures. No extra user-visible message or
Python semantic fallback occurred. Round 3 wrote and reopened 11 canonical
MemoryStatements.

Validated implementation commit: `PENDING_FINAL_COMMIT`.

V3.2 exact-span Formation is no longer active architecture. Its
`EvidenceStore` schema remains compatibility-readable and migratable; new
writes use `nollm_access_statement_v1`.

Core, Snapshot, Trace, History, and Audit behavior is unchanged. This task did
not implement Placement or Recall, preserve raw user transcripts, or establish
model semantic accuracy. Real-user quality review, revision/forget workflows,
cross-process Store coordination, and broader product integration remain open.
