# MT1-R12: Operational Safe Storage & Ingress Closure

## Contract: fd-anchored Storage

### Problem

R11 SafeStorage checks paths before read/write, but TOCTOU gaps remain:
a parent directory can be replaced with a symlink between check and use,
causing controlled writes to land outside the memory root.

### Solution: Handle-Anchored Authority

The memory root is opened once. The opened handle (OS file descriptor /
Win32 HANDLE) is the authority anchor, not the path string. All controlled
path traversal and I/O must derive from this handle.

On POSIX: `openat(dir_fd, name, O_NOFOLLOW)`, `renameat2`, `unlinkat`.
On Windows: `CreateFileW` with reparse-point rejection, verified final path,
`GetFileInformationByHandle` for inode identity, `FlushFileBuffers` for
directory durability.

### SafeRoot V2 Capability Operations

1. `open_existing_root` - open root dir, retain (st_dev, st_ino, st_gen)
2. `initialize_root` - create root, then open
3. `secure_traverse` - walk path segments, reject symlink/reparse at each level
4. `secure_read_regular` - open file via handle, verify identity, read, re-verify
5. `secure_read_json` - secure_read_regular + strict JSON parse
6. `secure_read_jsonl` - secure_read_regular + strict JSONL parse
7. `secure_create_only` - create new file, fail if exists (unless idempotent)
8. `secure_replace` - atomic write to verified parent, rename within parent
9. `secure_append_ledger` - fenced append within writer lock
10. `secure_unlink` - remove file within verified parent
11. `durable_mkdir` - mkdir + fsync parent directory
12. `durable_rename` - rename + fsync both parent directories

### Invariant: No Raw Path I/O in Production Modules

All MT1 production modules (archive, archive_manifest, source_spans,
legacy_extract, legacy_import, native_field, provenance, coverage,
validation) must route I/O through SafeRoot V2. Direct use of
`Path.read_bytes`, `Path.write_text`, bare `open`, `os.replace` is
forbidden outside SafeStorage itself and the approved whitelist.

### Platform Unsupported Behavior

If the runtime cannot provide handle-anchored no-follow guarantees,
the API returns `safe_storage_unsupported` and refuses active-memory
mutation / publication. It never silently falls back to path checking.

### Ingress State Schema (R12-05)

state.json fields: schema, batch_id, state (enum), updated_at (RFC3339 UTC),
request_hash, fencing_token.

Invalid state: structured `malformed_*` error, no raw exception, no
automatic state transition, no active HEAD left behind.

### Immutable Archive (R12-06)

Finalized snapshot: canonical manifest, archive objects, source-span
inventory are create-only / exact-byte idempotent. `mark_spans_linked()`
returns `unsupported_legacy_mutator`. Import projections live only in
publication packages.
