# Nollm Current Status

Date: 2026-09-10.

## Completed baseline

V3.14 native OpenClaw memory-slot integration plus the parity-preserving Q40 phase
kernel was merged through PR #4, main `e798a72b34f1d62725cc31163a4e5ee144656932`.
Its validated source `0c7d88a` passed 394 offline tests and three ownership/asset
gates (run 34456184728). This is completed work, not a task to restart. Six old
contained development branches were archived, four incompatible histories were
cold-stored, and the merged kernel/temporary transports were archived. Original
tips remain recoverable.

## Current usable-direction increment

Status: IMPLEMENTED, with admission tied to the corresponding PR/run.
Scope: LAB mathematical kernel and validation; no production geometry switch.

- `certified_overlap.py` encloses ideal adjacent-layer source-area shares using
  directed integer radical arithmetic and exact rational clipping.
- Every possibly positive target is enumerated from geometric bounds, independent
  of which targets the 96-sample kernel happens to hit. Positive, zero and
  unresolved overlap are kept distinct.
- Bounded precision refinement produces a per-request area-interval width or
  raises an explicit budget failure. Tight oracle intervals are not a claim of
  small production error.
- `compare_q16` encloses total variation and missed mass while retaining target
  identity. It measures against supplied normalized Q16 weights, including tiny
  true overlaps omitted by the production sampling.
- The runner executes the existing broad fixtures, existing Decimal oracle and
  current production kernel unchanged. Generated reports stay outside Git.

Derivation, input domain, numerical convention and reproducible commands:
[Ideal overlap enclosures](../architecture/CERTIFIED_OVERLAP.md).
The single active router is [ACTIVE_PROJECT.md](ACTIVE_PROJECT.md).
Exact test counts, broad measurements and final admission head belong to the
PR/workflow evidence, not a guessed completion percentage.

## Retained limits

The production Core still uses the admitted 96-sample Q40 approximation with its
existing Q16 semantics, boundaries and state identity. Lab is not imported by a
production package. A replacement integer evaluator, changed geometric outputs,
full phase-region atlas and stored-state migration have not been admitted here.
The new containment argument is executable and reviewable but not formally
verified in a proof assistant. Per-request certificates do not establish a
uniform whole-domain bound for the production approximation.

Evidence stays immutable. Semantic decisions stay with the real LLM/Host and
Access. Single-entry Unified Field Encounter and separate Physical Memory Layer /
Aggregation Order remain active. No semantic index, saved entry or fact-to-entry
mapping is introduced.

The native provider remains a development/beta baseline. Packaged platform
runtime, automatic capture/Formation migration, clean public install/update/
uninstall, current OpenClaw-version compatibility, Windows Provider Live and
ClawHub release still require separate verification. No Host/global configuration
or user workspace is changed by this increment. Historical V3.13 Live evidence
is not a present diagnosis; see the preserved
[V3_13_REV1_DIRECT_ACTIVATION_REPORT.md](V3_13_REV1_DIRECT_ACTIVATION_REPORT.md).
