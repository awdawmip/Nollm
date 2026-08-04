# Nollm Mainline And Active Asset Curation Report

Date: 2026-07-30

Status: `MAINLINE_ACTIVE_ASSET_CURATED_AT_1ee023341d90bdcca4172783047b31639ff402b5`

Capability status remains `AOLD_UNIFIED_FIELD_ENCOUNTER_IN_PROGRESS` with
`PROVIDER_LIVE_PENDING`.

## Mainline

- GitHub main before promotion: `3b9ebc3492fb0fb1877b1e3cadeb20212a55911d`.
- Verified curation main: `1ee023341d90bdcca4172783047b31639ff402b5`.
- Fast-forward commits: 329, comprising 324 preserved capability commits and 5 curation commits.
- Force pushes, rebases, squashes, merge commits, and history rewrites: 0.

## Assets

- Input tree: 2104 tracked files, approximately 25.3 MB.
- Curated evidence tree: 833 tracked files before this report.
- External archive: `NOLLM_HISTORICAL_ASSETS_20260730_7e60875.zip`.
- Archive: 1277 files, 16,834,376 canonical Git blob bytes, ZIP size 4,430,182 bytes.
- Archive SHA-256: `933C7248A969FF840781814E5C3B6BA2C3B1DF68C2B4CE888DD60258E5DFD43A`.
- Input bundle SHA-256: `1B0C6B4D95256AE0D8C4AECECD7489BAD8424C7BD61A2B02C46BEA2BEC888269`.
- Plan retained: 279 active, 5 active fixtures, 60 legacy regressions, 480 migration assets, and 4 blocked dependencies.
- Largest archived roots: docs 483, lab 269, reference 228, validation 147, examples 88, experiments 53, tools 5, and four root F0 receipts.
- Full archive entry SHA, Git blob, source-commit, count, and byte verification passed.

## Branches And Worktrees

- Local deleted: `codex/aold-unified-field-encounter-read-write-duality`.
- Remote deleted: `codex/grf-unified-roadmap-full-implementation`, `codex/grf7-global-sharded-field-real-runtime`, `codex/grf7r-evidence-integrity-real-global-runtime`, `codex/grf7r2-final-closure`, `codex/grf7r3-compact-evidence-handoff`, `codex/grf8-real-data-productization`, and `codex/hx1-trusted-host-staged-plan-execution-bridge`.
- Retained remote evidence branches: `evidence/w2-02-isolated-active-trial-20260627T1528Z`, `evidence/w2-03-target-bound-active-trial-20260628T073600Z`, and `evidence/w2-03r-main-agent-active-cutover-20260628T094800Z`; each has one commit not in main.
- All 22 tags were preserved.
- The linked V3.12 worktree registration was removed through `git worktree remove`. Windows reported a long-path deletion error after unregistering it, so the non-Git orphan directory remains at `<NOLLM_ROOT>\workspaces\nollm_v312_unified_field_encounter_work` and was not force-deleted.
- Independent verification clones and five repositories with tracked dirty state were preserved.

## Engineering Verification

- Core: 88 passed.
- Snapshot and Trace: 10 passed (7 + 3).
- Access: 150 passed, 8 deprecation warnings.
- OpenClaw Python: 92 passed.
- OpenClaw Node: 63 passed, 2 skipped; build and plugin check passed.
- GRF compatibility: 112 passed.
- M0, architecture, and hygiene: 53 passed.
- Compileall passed; six distribution JSON manifests parsed successfully.
- Ownership manifest: 833/833 before this report, zero unclassified.
- Boundary: zero production violations, `cycles_production=[]`, `cycles_all=[]`; 10 migration findings retained.
- Active tree gate: zero violations; Markdown links resolve; root `AGENTS.md` is exactly 0 bytes with the empty-file SHA-256 and Git blob.

## Actual Progress

```text
CORE 0% | SNAPSHOT 0% | TRACE 0% | ACCESS 0% |
HISTORY 0% | AUDIT 0% | OPENCLAW 0% | LAB +5% | DISTRIBUTIONS +10%
```

LAB and DISTRIBUTIONS reach the task's 99% governance targets. No production
implementation or migration code was changed or deleted, no unmerged branch
was deleted, and no functional completion beyond the existing offline V3.12
evidence is claimed. Provider/Host Live was not run.
