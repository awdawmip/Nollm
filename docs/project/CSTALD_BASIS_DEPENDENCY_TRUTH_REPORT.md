# CSTALD Basis And Dependency Truth Report

## Vector And Progress

Expected and actual:

```text
CORE +5% | SNAPSHOT 0% | TRACE 0% | ACCESS 0% |
HISTORY 0% | AUDIT 0% | OPENCLAW 0% | LAB +5% | DISTRIBUTIONS +5%
```

All module deviations are zero. Actual completion is Core 80%, Snapshot 50%,
Trace 40%, Access 60%, History 10%, Audit 10%, OpenClaw 25%, Lab 55%, and
Distributions 45%.

## Active Basis And Manifest Truth

- Active project book: `NOLLM_PROJECT_BOOK_V3_1_CORE_PURITY_AND_EVOLVING_BASELINES_20260711.md`.
- Current task: `tasks/NOLLM_CSTALD_BASIS_DEPENDENCY_TRUTH_TASK_20260712.md`.
- V3.0 and V2.2 books are `LEGACY_REFERENCE / SUPERSEDED`.
- `AGENTS.md` is generic, concise, path-free, and contains no project-stage rules.
- `ACTIVE_PROJECT.md` has five unique existing links with single document roles.
- All six active governance paths, including the Basis itself, are classified
  `ACTIVE`, `public_api=governance`, and `review_status=CODE_REVIEWED`.
- Unlinked tasks and reports are historical; no M0C1 or M1 filename heuristic remains.
- Ownership manifest is 1479/1479 with zero unclassified files.

## Public Dependency Truth

- Lab private Core submodule imports: 0.
- Core public API additions for Lab: 0.
- Lab owns compile-only axial/ring, Q16 normalization, metadata, template values,
  canonical JSON helper, and research definitions.
- Parity reads public `KernelRegistry`, `runtime_profile`, and `expand_template`.
- Artifact SHA-256 remains
  `21659434328e457e0d868ddc1dcbf64484739ffeb64eb61eb62197616ddf0eba`.
- Geometry parity remains 9/9 and state identity is unchanged.

## Capability Evidence

```text
validated_code_commit = 7ff9690edeca71806bf5783787ef81367b9eb167
validated_code_tree_digest = b8a17134c494d3610c306723281bcdede7c130de41ec010d290a02e093ecbd27
verified_capabilities = 25 / 25
```

The final bundle HEAD is the commit containing this report and is recorded by
the delivered bundle HEAD ref. Embedding that commit's own hash in its tree
would be self-referential; the delivery response and `git bundle list-heads`
provide the exact value.

## Verification

```text
Core 39 passed | Snapshot 7 passed | Trace 3 passed | Access 32 passed
M0 32 passed | architecture/forbidden/hygiene 8 passed | GRF 112 passed
geometry parity 9/9 | capability validator 25/25 | Minimal E2E passed
production violations 0 | production cycles [] | migration findings 7
```

## Limitations

This task did not validate malicious Python isolation, cross-process locking,
crash recovery, OpenClaw Live, real LLM placement, memory quality, long corpora,
PB scale, History/Audit products, installers, or remote repository splitting.

This report does not claim sealing, final closure, or automatic entry to a
later stage.
