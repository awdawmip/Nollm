# LD Asset Taxonomy Truth Report

Date: 2026-07-12

Input baseline: `bdd90499b240eb65ecc089059c249a8eb862d570`

Validated code commit: `7ff9690edeca71806bf5783787ef81367b9eb167`

Validated code tree digest:
`b8a17134c494d3610c306723281bcdede7c130de41ec010d290a02e093ecbd27`

## Classification

All 562 Lab-owned assets use one of nine explicit classes. Current executable
assets are bound to concrete package, governance, Lab, compatibility, or
repository gates. Broad Lab-owned directories no longer imply ACTIVE status.

| Asset class | Count | Gated | Lifecycle |
| --- | ---: | ---: | --- |
| `ACTIVE_LIBRARY` | 4 | 4 | ACTIVE |
| `ACTIVE_TOOL` | 1 | 1 | ACTIVE |
| `ACTIVE_FIXTURE` | 0 | 0 | ACTIVE |
| `ACTIVE_TEST` | 67 | 67 | ACTIVE |
| `ACTIVE_VALIDATION` | 3 | 3 | ACTIVE |
| `ACTIVE_REPOSITORY_TOOL` | 4 | 4 | ACTIVE |
| `LEGACY_REGRESSION` | 53 | 53 | MIGRATION_ASSET |
| `LEGACY_REFERENCE` | 391 | 0 | HISTORICAL |
| `HISTORICAL_RESULT` | 39 | 0 | HISTORICAL |

Gate coverage is 132/132 for classes requiring execution. Legacy references
and historical results have no active gate. No historical file was deleted.

## Progress

Expected and actual vector:

```text
CORE 0% | SNAPSHOT 0% | TRACE 0% | ACCESS 0% |
HISTORY 0% | AUDIT 0% | OPENCLAW 0% | LAB +5% | DISTRIBUTIONS +5%
```

Measured deviation is zero. Actual completion is Core 80%, Snapshot 50%, Trace
40%, Access 60%, History 10%, Audit 10%, OpenClaw 25%, Lab 55%, and
Distributions 45%.

## Verification

- Manifest: 1489 tracked rows, unclassified 0.
- Boundary: production violations 0, production cycles empty, migration
  findings 7.
- Public contract/import smoke: 11 executable assets checked, errors 0, import
  failures 0.
- Package tests: Core 39, Snapshot 7, Trace 3, Access 32.
- Governance and compatibility: M0 43, architecture 8, GRF 112.
- Geometry parity 9/9, Core capability 25/25, Minimal E2E passed.
- Compiled template artifact SHA-256:
  `21659434328e457e0d868ddc1dcbf64484739ffeb64eb61eb62197616ddf0eba`.
- Compileall, manifest read-only check, and `git diff --check` passed.

Bundle and clean-clone results are bound to the delivered HEAD; the exact
bundle digest is recorded by delivery verification.

## Limits

OpenClaw Live, real LLM placement, cross-process recovery, memory quality,
corpora, PB scale, installers, and version negotiation remain unvalidated. A
next candidate action requires a separately approved taskbook.
