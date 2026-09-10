# Nollm Current Status

Date: 2026-09-10

## Current baseline and active work

The implementation baseline is V3.14 native OpenClaw memory-slot integration at
`91bd14ab394e87931b45baaaa87671f30fcfd706`, following merged PR #2
(`6c4f93cef77bb2c03c98777015416843e5bbaf8d`). PR #1 / V3.13 is inherited
history, not an open competing mainline task.

The current user-authorized task is to build a new kernel, integrate validated
compatible work and cold-store branches whose unique history should not enter
main. Its development branch is `kernel/q40-phase-20260910`; the governing
amendment is in `docs/project/ACTIVE_PROJECT.md`.

Implemented in this branch:

- A parity-preserving Q40 phase kernel replaces repeated per-source sample
  transformation with two compiled directional stencils and a counted relative
  footprint. Even integer anchors preserve half-to-even midpoint behavior.
- The existing 96-sample approximate geometry contract, thresholds, all output
  fields, coordinate limits, single-entry traversal and canonical state identity
  are preserved. This is not a claim of certified exact real-area Coverage.
- Cache clearing now discards every derived kernel cache; no cache is memory
  truth and no semantic or source-to-entry index is introduced.
- Five additional independent integer-reference and boundary/cache tests were
  added while retaining the existing regression tests. The isolated five-test
  run passed. Full package and repository gate outcomes are recorded by the
  corresponding PR/workflow; an implementation checkpoint is not Live approval.

## Unchanged capability boundaries

V3.12 Unified Field Encounter remains the unified read/write operation. The
V3.14 integration direction is OpenClaw's exclusive native memory slot with
standard `memory_search` / `memory_get`, not a second custom memory tool.
Evidence stays immutable, semantic decisions stay with the real LLM/Host and
Access, and Core stays deterministic and semantic-blind. Physical Memory Layer
and Aggregation Order remain distinct.

The native provider package remains a development/beta capability baseline.
Packaged platform runtime, automatic capture/Formation migration, clean public
install/update/uninstall, Windows Provider Live and ClawHub release still require
separate validation. This kernel task changes no Host installation or global
OpenClaw configuration and makes no new current-version compatibility claim.

The old V3.13 Direct Activation run reported `run_scope_unavailable`; that is
historical evidence, not proof of the current V3.14 provider's Live behavior.
The preserved report is
[V3_13_REV1_DIRECT_ACTIVATION_REPORT.md](V3_13_REV1_DIRECT_ACTIVATION_REPORT.md).
No old environment observation or empty-AGENTS statement is silently carried
forward as current fact.

## Admission and next mathematical boundary

Before promotion, validate the kernel against the frozen predecessor, retain
its exact integer output contract, run available package/governance gates and
record the exact tested commit. Do not call a partial or pending test suite
passed. Compatible already-contained branches need no duplicate merge; unique
branches must remain recoverable before any original ref is removed.

Certified area-overlap evaluation, explicit quadrature error bounds, any
phase-region atlas and any changed geometric contract remain distinct future
work. The ideal eight-layer transform identity does not authorize an exact
shortcut through rounded Q40 steps. Memory-quality improvement, large-scale
performance and Provider Live are not established by kernel parity alone.
