# Nollm Current Status

Date: 2026-07-11

The active stage is M0 Module Ownership and Monorepo Separation. Nollm remains
one Git repository with explicit package, integration, lab, distribution, and
legacy boundaries. No GitHub repository split has been performed.

## Active Decisions

- Core owns geometry current state and policy-free public ports only.
- Snapshot, Trace, Access, History, Audit, OpenClaw, Lab, and Distributions are
  separate ownership domains.
- OpenClaw Live Integration and all long LLM corpus execution are paused.
- GRF8 is an engineering checkpoint, not accepted architecture.
- Evidence-first V2/V2.1/V2.2 and old GRF/OpenClaw handoffs are historical or
  superseded migration references.
- M1, under a separate taskbook, owns semantic extraction and blocked-path
  deletion.

The authoritative M0 machine records are the ownership manifest,
`config/module-boundaries.json`, and `M0_BOUNDARY_BASELINE.json`.
