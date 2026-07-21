# CAOLD Runtime Integrity And Atomic Proposition Growth Report

Date: 2026-07-21

Status: `RUNTIME_INTEGRITY_AND_RELATION_ENTRY_COLLISION_CHECKPOINT_AT_c40f8bf6a5be6184e5e56236c96d2817fed4bee5`

## Scope And Baseline

- Input bundle SHA-256: `a795bb9941c8765b26dda8373678b66f2ccf62a2a30372f193d2e604a6934a28`.
- Input HEAD: `db2b5b0c25d8d527a249de90c6555aeaf686f618`.
- Work branch: `codex/caold-runtime-integrity-atomic-proposition-growth-evidence-closure`.
- Implementation commits before final evidence/governance closure:
  - `4d4d0b221e08d387f7215adfe696207be58b4cc8` Core runtime integrity and Junction limits.
  - `81cec3a7b6375b78a5d7055c81f6b477e8cca92b` Access rollback diagnostics and commit state.
  - `805df7574d8fc6b7d7f347b2d37e7b5c985fc715` recoverable OpenClaw absorption.
  - `3043d9a78d3fb88f89c8c4d54904c87b4e84940c` live/frozen Evidence separation.

The task preserves Rev3 Prompt-bounded Writer/Cartographer, independent seed,
realized Junction, and relation-entry Recall. It adds no multi-cell footprint,
multi-entry Recall, persistent Lens, Topic/Entity, semantic index, graph,
embedding, query/fact map, network queue, or database.

## Reliability Closure

Core rejects Trace callback mutation, nested batch/import, and close while an
operation is active. Callback exceptions cannot silently commit state. Public
Junction ranking evaluates the complete finite candidate universe before the
caller output limit, and active radius behavior is consistent.

Access holds a Core-owned operation lease across cross-store composition.
Fatal rollback exposes the original error, each rollback failure, and an
explicit unknown commit state; the affected runtime becomes unusable. Direct
`BaseException` handling is documented as unknown state. Durable readback
reports reopen verification or committed-but-unavailable without duplicate
admission. Corrupt Statement bytes are item-level Recall errors. Revision uses
fresh Atlas state and explicitly retires current/supporting aliases while
preserving immutable Statement files.

Capture recovery preserves batch identity, recovers stale processing, and
resumes only unfinished Captures after terminal-state interruption. Writer JSON
correction is format-only. Provider identity comes from the actual resolved
child session. Live Evidence is run-scoped; immutable freeze requires writer
rotation or disablement and exact-byte stability.

## Real Provider Run

Host: Windows, OpenClaw `2026.6.11`, plugin `0.17.0`, Provider/model
`meituan/LongCat-2.0`. Four pre-existing global cron jobs were disabled before
the accepted run. The V5 workspace remained isolated from historical V4 data.

Nine ordinary atomic chats produced:

- 9 immutable Captures;
- 9 Statements, each with one Atom, one Handle, and one Cell;
- 9 durable commits with `commit_state=reopen_verified`;
- 1 `related_growth` at `default:L0:-1,0` from the Tokyo arm;
- 8 `independent_seed` placements;
- 1 structured Cartographer retry that converged as attempt 2 on the same Capture ID;
- 0 duplicate or orphan admissions.

The Writer introduced one semantic date error in the weather arm, changing an
assistant-derived fact to 2026-07-20. The raw output and validated plan are
preserved in frozen Evidence; no Python correction altered that semantic value.

## Recall Counterexample

Capture was disabled during Recall to preserve the nine-write fixture. The
fallback formation path was observed on NONE but produced
`statement_store_write_count=0`; durable state stayed at 9 Statements and 9
Captures. Six post-growth single-entry Recall attempts used at most one hidden
Provider call each:

- selected entry count: 1 distinct Cell, `default:L0:4,0`;
- T0 Statement recalls: 0;
- non-empty selected paths: 0;
- correct NONE outcomes: 1;
- restart preserved 9 Statements and 9 Captures, but repeated the same empty-path selection.

Tokyo, time, weather, and unrelated prompts all selected the meeting-record
Cell. Visible answers were not used as geometry evidence. The required three
distinct relation entries with path length at least 2 to the same T0 Handle
were not realized.

Rev4 reclassifies this as an entry-identity collision checkpoint, not a
one-cell Provider counterexample. Region-local support entry IDs were silently
overwritten by fast Recall before the Provider selected an entry. Gate D
remains historical `IN_PROGRESS` evidence and does not authorize multi-cell.
It does not authorize multi-cell or any DX-style repair inside this task.

## Evidence Lifecycle

- Frozen live Evidence: 106 lines, 88,365 bytes.
- Frozen live Evidence SHA-256: `aaf5f9f68c55fb3a3eeb0043e591729f3f145cfe0216e2b1e270d9ca71e498a2`.
- Frozen Capture/state snapshot: 39 files, 35,083 bytes (38 exact source
  records plus the compact path manifest).
- Capture/state aggregate SHA-256: `faa638dc63f7e4a6c6f20fa4ef64d5c8f740b7db4188d38796f2f7a1d6c762ef`.
- Gateway probe before/after freeze: no listener and no Gateway process.
- Active writer paths at freeze: none.
- Operator attestation: none; all freeze facts are machine-observed.

The Windows process probe initially included the freeze command itself because
its arguments contained `--gateway-port`. The detector was narrowed to the real
Node OpenClaw `gateway` command and regression-tested before the accepted
freeze. Source and frozen SHA-256 match, and the frozen artifact is read-only.

## Verification

- Core + Access: `207 passed`, 8 deprecation warnings.
- Snapshot/Trace/Audit/History packages: `10 passed`.
- OpenClaw Python: `53 passed`.
- OpenClaw Node: `49 passed`.
- Lab: `35 passed`.
- Evidence verifier/freeze focused tests: `4 passed`.
- M0: `45 passed`.
- Ownership Manifest: `2030` tracked files and rows, `0` unclassified.
- Boundary checks: `0` production violations and `0` production cycles.
- The complete `reference/python/tests` collection contained `1834` nodes.
  It timed out after 15 minutes; a second run excluding
  `test_nollm_test_matrix.py` timed out after 20 minutes without a failure
  summary. This is recorded as an unresolved long-running-suite diagnostic,
  not as a passing result.
- Clean-clone tests and bundle verification are recorded in the final delivery
  evidence.

The Rev3 10/10 target-hidden causal fixture remains an accepted synthetic
checkpoint. The current live run does not replace or weaken it; it shows that
free atomic Provider growth did not reproduce the required three-arm field.
