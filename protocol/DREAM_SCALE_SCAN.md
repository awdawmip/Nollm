# Dream Scale Scan

## Definition

Dream scale scan is an explicit traversal plan record for inspecting candidate
geometry across layers.

## Scope

- Record linear scale scan steps.
- Record bounded addresses per step.
- Preserve stop reasons and candidate status.

## Non-Scope

Dream scale scan is not Core recall. It is not tree descent, semantic scoring,
or hidden search state.

## Records

```text
ScaleScanStep(layer, chart_id, addresses, reason)
ScaleScanPlan(plan_id, shard_id, steps, stop_reason, status)
```

## Boundary

Steps are explicit records. There is no leaf-node assumption, no parent-child
hierarchy, no card writing, and no recall integration.
