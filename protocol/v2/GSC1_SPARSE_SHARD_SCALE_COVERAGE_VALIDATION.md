# GSC1 Sparse-Shard Scale-Coverage Validation Protocol

GSC1 defines a finite synthetic validation protocol for sparse occupancy labels over DG1 coverage kernels.

## Protocol Inputs

The protocol accepts only explicit host-provided finite marker tuples in the fixed GSC1 window. The fixture defines the complete input set and performs no discovery, scanning, persistence, admission replay, or recall.

## Protocol Operation

For each marker, layer gap, base layer, phase sample, and layer phase policy:

1. Build source and target charts from sealed DG1 `ScaleRotationSchedule`.
2. Construct the source cell from the marker axial coordinate.
3. Construct a finite target disk of radius `4` around the nearest target axial coordinate.
4. Compute the `fine_to_coarse` coverage distribution with sealed DG1 `compute_distribution(...)`.
5. Record canonical target references, kernel weights, residual mass, and residual reasons.

Support collision summaries are derived only by grouping observed finite target references by marker id inside the same fixed window. A collision means shared diagnostic support only. It is not a merge, ownership, parent-child, identity, semantic, memory, or recall relationship.

## Purity Boundary

The protocol imports DG1 geometry only. It does not import or call Evidence, Capture, Cortex, Admission, Field, Assembly, Recall, adapters, runtime, network, database, cache, or OpenClaw code.

## Report Boundary

The baseline report is a deterministic Markdown projection of the computed finite observations and summaries. Presentation noise-floor rendering is report-only and does not replace raw float64 validation values.
