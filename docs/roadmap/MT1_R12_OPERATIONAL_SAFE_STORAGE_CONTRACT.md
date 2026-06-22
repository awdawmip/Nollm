# MT1-R12: Operational Safe Storage & Ingress Closure

## Contract Summary

R12 upgrades Nollm MT1 storage from path-check-based safety to
handle-anchored capability-based safety. The root directory fd/handle
is the authorization anchor, not the path string.

## Platform Model

On Windows (primary deployment), POSIX `dir_fd` and `O_NOFOLLOW` are
unavailable. R12 uses Win32 handle-based operations:

- `CreateFileW` with `FILE_FLAG_BACKUP_SEMANTICS` to open directories
- `GetFileInformationByHandle` for identity (volume serial + file index)
- Reparse point detection via `FILE_ATTRIBUTE_REPARSE_POINT`
- `FlushFileBuffers` for file fsync
- `FlushFileBuffers` on directory handle for directory fsync
- File identity verified after every open to detect TOCTOU swaps

On POSIX platforms, `dir_fd`, `O_NOFOLLOW`, and `fstat` provide
equivalent guarantees natively.

## SafeRoot V2 Capability Model

1. Root directory opened once; handle + identity retained.
2. All controlled paths resolved relative to the root handle.
3. Each path segment verified: no symlink/reparse, correct type.
4. Regular files checked: `st_nlink == 1` for authoritative artifacts.
5. Atomic writes use temp files within the verified parent directory.
6. File and directory fsync after every mutation.
7. Any verification failure = structured error, no partial state.

## What R12 Fixes (from R11 Review)

- P0: TOCTOU in safe_atomic_write (parent swap after check)
- P0: Read APIs bypass SafeStorage (path.read_bytes after containment)
- P0: Hard-linked authoritative artifacts accepted by admission
- P0: Concurrent planner crashes and ledger loss
- P0: Torn-plan permanently poisons deterministic batch
- P0: Ingress state schema not closed, raw exceptions leak
- P1: mark_spans_linked mutates immutable archive inventory
- P1: Read APIs implicitly create memory root
- P1: No directory fsync (crash durability)
- P1: Direct Path I/O still exposed in production modules
- P2: Invalid inputs create root before failing

## Ingress State Schema

All ingress state files must have closed schema with strict validation:
- import-request, state, import-receipt, publish-handoff,
  publish-journal, recovery record, ledger event
- Unknown fields, wrong types, invalid enums = structured fail-close
- No raw exceptions to callers

## Immutable Archive Boundary

Archive snapshot + canonical span inventory = immutable archive fact.
Import projections, publication links, shard lifecycle state belong
only to the publication package, never to the archive inventory.

## Delivery

Single self-contained git bundle with project branch + synthetic
evidence orphan branch. No ZIP, no second bundle, no real memory data.
