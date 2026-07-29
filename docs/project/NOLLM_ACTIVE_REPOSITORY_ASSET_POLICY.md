# Nollm Active Repository Asset Policy

Date: 2026-07-30

This is the single policy for assets in the current Git tree. It changes no
production capability and does not redefine the V3.12 Provider Live gate.

## Allowed In The Current Tree

- Active source, package tests, and required fixtures.
- Current first principles, project book, architecture, route, status, ledger,
  task, capability record, module charters, and distribution composition.
- Migration implementations, compatibility re-exports, legacy regressions,
  and current Wire witnesses that remain required by active gates.
- Executable governance tools and a bounded set of stable examples.

## Stored Outside The Current Tree

- Git bundles and ZIP, TAR, TAR.GZ, TGZ, or 7z archives.
- Frozen Live JSONL, run logs, Provider transcripts, round receipts, delivery
  receipts, generated report copies, and external artifact manifests.
- Superseded task books, status snapshots, starting-state records, experiment
  results, model corpus output, and historical validation evidence.
- Temporary worktrees, caches, databases, sessions, and runtime state.

Historical bytes remain recoverable from Git history and from the verified
external archive named by the current curation report. They must not be copied
back into the active tree merely for convenience.

## Retained Migration Assets

An asset classified as `MIGRATION_ASSET`, `LEGACY_REGRESSION`, or
`BLOCKED_ACTIVE_DEPENDENCY` remains in Git until a later authorized gate proves
its replacement and removes every active dependency. Directory names, age, or
visual clutter are not deletion authority.

## External Output Roots

```text
NOLLM_ARTIFACT_ROOT=D:\Nollm\artifacts
NOLLM_ARCHIVE_ROOT=D:\Nollm\archives
NOLLM_BUNDLE_ROOT=D:\Nollm\bundles
```

Tests use temporary directories. Repository tools fail closed when a durable
generated output resolves inside the Git worktree.

## Enforcement

`tools/check_active_tree_assets.py` enforces archive, frozen-evidence, receipt,
generated-JSONL, fixture-allowlist, and zero-byte `AGENTS.md` rules. The
ownership manifest and active curation plan remain the machine-readable source
for lifecycle and removal decisions.
