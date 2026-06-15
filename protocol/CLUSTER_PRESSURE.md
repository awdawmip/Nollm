# Cluster Pressure

## Definition

Cluster pressure is deterministic metadata summarizing local dream placement
candidate density.

## Scope

- Count placement candidates by chart address.
- Record explicit pressure values.
- Propose coarse emergence candidates for inspection.

## Non-Scope

Cluster pressure is not semantic truth. It does not create clusters
automatically, does not write cards, and does not create parent-child geometry.

## Records

```text
ClusterPressureSample(chart_id, address, placement_count, pressure, reasons)
CoarseEmergenceCandidate(chart_id, center, radius, pressure_sum, sample_count, status)
```

`CoarseEmergenceCandidate.status` defaults to `candidate`.

## Boundary

Pressure records are explicit diagnostics only. They are not recall, hidden
indexing, ontology generation, or automatic memory rewriting.
