# Nollm

> Not an LLM. A notebook for LLMs.

Nollm is in the M0 modular-monorepo stage. Module ownership and dependency
boundaries are current; the repository has not been physically split on GitHub.

## Current Modules

- `packages/nollm-core`: deterministic geometry current state and public ports
- `packages/nollm-snapshot`: policy-free state snapshot operations
- `packages/nollm-trace`: optional observability sinks
- `packages/nollm-access`: product and host decision boundary
- `packages/nollm-history`: optional semantic history boundary
- `packages/nollm-audit`: optional audit boundary
- `integrations/openclaw`: OpenClaw adapter assets
- `lab/nollm-lab`: corpora, tests, benchmarks, and migration assets
- `distributions`: composition metadata only
- `legacy/quarantine`: preserved uncertain migration assets

See [ARCHITECTURE.md](ARCHITECTURE.md), the module charters under
`docs/architecture/modules/`, and the complete tracked-file ownership manifest
under `docs/architecture/module-ownership/`.

## Current Limits

OpenClaw Live Integration and long LLM corpus work are paused. GRF8 is an
engineering checkpoint, not accepted architecture. Evidence-first V2, older GRF
handoffs, and previous OpenClaw taskbooks are historical or superseded inputs to
the ownership audit, not current architecture.

M1 will extract mixed responsibilities and remove blocked paths. M0 does not
perform those semantic rewrites.

M1 is not started. It requires a separately approved taskbook after M0C1 closes.

## Validation

The repository-wide diagnostic remains:

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
python run_tests.py
```

The command runs with `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`. It is a
legacy-inclusive repository diagnostic, not the M0 component acceptance gate.
It is also not the primary V2 component acceptance gate; V2 is historical under
M0.
Historical delivery-grade V2 acceptance used the TQ1 matrix and a parentless evidence capsule;
those terms do not define the M0 gate.
M0 uses the scoped GRF, Snapshot/Trace, package import, boundary, and hygiene
gates recorded in `docs/validation/M0_BEHAVIOR_PRESERVATION_REPORT.md`.
