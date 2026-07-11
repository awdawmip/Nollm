# Nollm Architecture

The current architecture is a modular monorepo. GitHub repositories have not
been physically split.

## Dependency Direction

```text
core <- snapshot
core trace contracts <- trace implementations
core <- access
access <- history
access contracts <- audit
access <- openclaw
all modules <- lab
modules <- distributions (composition only)
```

Core owns deterministic geometry current state, bounded geometry-entry recall,
atomic current-state writes, and Snapshot/Trace ports. It does not own source,
host, user, session, semantic placement, history, audit, or trace persistence.

The machine-readable rules are in `config/module-boundaries.json` and enforced
by `tools/check_module_boundaries.py`. Existing cross-boundary debt is frozen in
`docs/architecture/module-ownership/M0_BOUNDARY_BASELINE.json`; new debt fails
the checker.

## State Boundaries

- Snapshot stores structural current-state copies; it does not define history.
- Trace stores optional operation observations; it is not fact or audit state.
- History owns semantic version chains; it is not Snapshot or Trace.
- Audit owns host/user/session action records; Core does not depend on it.
- Access owns product decisions and maps them to public Core commands.

## Historical Routes

Evidence-first V2/V2.1/V2.2, GRF8, older GRF handoffs, and paused OpenClaw Live
Integration taskbooks are preserved as historical or superseded migration
inputs. See `docs/history/M0_SUPERSEDED_ROUTE_INDEX.md`.
