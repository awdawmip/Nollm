# Nollm V3.8 Final Regression And Delivery Gate 7 Report

**Date**: 2026-07-15
**Branch**: `codex/caold-translation-covariant-physical-coverage-reuse`
**Status**: `IN_PROGRESS`

## Fixed Regression Matrix

| Suite | Result |
|---|---:|
| `packages/nollm-core/tests` | 52 passed |
| `packages/nollm-snapshot/tests` | 7 passed |
| `packages/nollm-trace/tests` | 3 passed |
| `packages/nollm-access/tests` | 76 passed, 8 deprecation warnings |
| `integrations/openclaw/formation-loop/tests` | 37 passed |
| `reference/python/tests/m0` | 45 passed |
| DG1 focused geometry tests | 46 passed |
| OpenClaw Node tests | 19 passed |
| OpenClaw `plugin:check` | passed |

The first parallel pytest attempt was invalid because repository-wide cleanup
hooks raced on Windows and produced `WinError 32`. The fixed matrix was rerun
serially. M0 was run with this candidate worktree's `reference/python` first on
`PYTHONPATH` to avoid an unrelated editable import pointing at the original
checkout.

## Geometry Runners

| Runner | Result SHA-256 |
|---|---|
| GVR1 | `06d01f464a871c9847f58c2165326e10330987f034d9bc2ecbbccdb6b2868cb0` |
| GRA1 | `8f16323a76f71dd15490f5cbf9cff3358020eb3386d1f3405e4264de6592304d` |
| GRC1 | `cc3ffed1f1b84d3f8e7ce553be46e8f0cfca05fcd6d3bad1c1dc74bd7d38cb04` |
| GKD1 | `f424a2f9bfd2cd414ba67754263dbdd8bde1246c8fe5f3545f5084eea9218276` |
| GPR1 | `09c128dff42a5ea89ad2981f65226d3e736e498343f744a5f6688d7ff24d71f6` |

The outputs are external to Git under
`C:\Users\chaos\nollm_v38_gate7_outputs`.

## Governance

```text
ownership manifest: tracked=1812 rows=1812 unclassified=0
production boundary violations: 0
production cycles: 0
V3.8 authority and no-shortcut checks: passed
reusable geometry assets: 17 matched, 0 failures
git diff --check: passed
```

The M0 governance tests were updated from stale V3.7 assertions to the active
V3.8 route committed by Gate 0. The two new Lab tools now have explicit
ownership gates and validator targets.

## Actual Progress Vector

```text
CORE +10% | SNAPSHOT 0% | TRACE 0% | ACCESS +5% |
HISTORY 0% | AUDIT 0% | OPENCLAW +3% |
LAB +15% | DISTRIBUTIONS +5%
```

Core, Access, Lab, and Distribution targets were met. OpenClaw remains at 88%
because P1 did not reach placement. This prevents the completion tag even
though the controlled single-entry cross-layer Recall succeeded.

The only truthful delivery tag is:

```text
CAOLD_TRANSLATION_COVARIANT_PHYSICAL_COVERAGE_REUSE_IN_PROGRESS_AT_<HEAD>
```
