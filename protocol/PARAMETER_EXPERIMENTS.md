# Parameter Experiments

## Definition

Parameter experiments are deterministic numeric diagnostics for candidate
Dream Geometry regimes.

## Scope

- Record beta and theta candidate regimes.
- Evaluate rotation-cycle hits.
- Evaluate side-length ratio after a bounded layer count.
- Rank diagnostic results deterministically.

## Non-Scope

Parameter experiments do not lock final geometry policy, do not create
parent-child nesting, and do not integrate with recall or placement.

## Default Regimes

- `2^(1/4) + 15 deg`
- `2^(1/4) + 22.5 deg`
- `sqrt(2) + 15 deg`
- `phi + 15 deg`
- `sqrt(3) + 30 deg benchmark`

## Boundary

These records are experimental diagnostics only. They are not semantic truth,
not a hidden index, and not automatic geometry policy.
