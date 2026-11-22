# Nollm Active Repository Asset Policy

Updated: 2026-11-22

This is the single policy for assets in the current Git tree. It changes no
production capability and does not redefine the V3.12 Provider Live gate.

## Allowed In The Current Tree

- Active source, package tests, and required fixtures.
- Current first principles, project book, architecture, route, status, ledger,
  task, capability record, module charters, and distribution composition.
- Migration implementations, compatibility re-exports, legacy regressions,
  and current Wire witnesses that remain required by active gates.
- Executable governance tools and a bounded set of stable examples.
- The active development notebook, **速记本**, at `sujiben/`, including its
  complete native field, current bindings, expression history, and source references.
- Working research fields that are still used, including
  `lab/nollm-lab/repository_memory/enterprise_math/field/`.

## Stored Outside The Current Tree

- Git bundles and ZIP, TAR, TAR.GZ, TGZ, or 7z archives.
- Frozen Live JSONL, run logs, Provider transcripts, round receipts, delivery
  receipts, generated report copies, and external artifact manifests.
- Superseded task books, status snapshots, starting-state records, experiment
  results, discarded model output, and historical validation evidence.
- Temporary worktrees, caches, sessions, and generated run state outside the
  explicitly maintained working fields above.

LLM authorship is not an archival criterion. The current notebook remains on
the active development line and is revised through the native memory path.
Archive older code or experiments only after checking that current code,
validation, and project workflows no longer need them. Installing the runtime
does not copy or choose these working fields; callers supply `--field`.

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
NOLLM_ARTIFACT_ROOT=<NOLLM_ROOT>\artifacts
NOLLM_ARCHIVE_ROOT=<NOLLM_ROOT>\archives
NOLLM_BUNDLE_ROOT=<NOLLM_ROOT>\bundles
```

Tests use temporary directories. Repository tools fail closed when a durable
generated output resolves inside the Git worktree.

## Enforcement

`tools/check_active_tree_assets.py` enforces archive, frozen-evidence, receipt,
generated-JSONL, fixture-allowlist, and current `AGENTS.md` entry rules. The
ownership manifest and active curation plan remain the machine-readable source
for lifecycle and removal decisions.
