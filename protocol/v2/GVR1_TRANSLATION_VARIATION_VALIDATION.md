# GVR1 Translation Variation Validation

GVR1 validates finite translation sensitivity for the sealed engineering baseline B without changing production geometry.

## Construction Rule

For every `(gap, phase, policy, base_layer, source_offset)`:

- `base_layer in range(0, 17-gap)`
- `source_offset in disk(AxialCoord(0, 0), 1)`
- `source_layer = base_layer + gap`
- `source_phase = policy.phase_for_layer(phase, source_layer)`
- `target_phase = policy.phase_for_layer(phase, base_layer)`
- source and target cells are constructed with sealed DG1 chart and hex-cell APIs.
- coverage is computed with sealed DG1 `compute_distribution(...)`.

The row distribution count is exactly `7 * (17-gap)`.

## Metrics

Rows are summarized with sealed DG1 `summarize_distributions(...)`. Per-offset variation envelopes use sealed DG1 `distribution_metrics(...)` and ordinary finite `min`, `max`, and `span` aggregation over per-offset means.

`phase_recurrence_score` is a chart/phase schedule diagnostic over legal base layers and is not multiplied by source-offset count.

## Non-Claims

GVR1 does not prove full-plane translation invariance, does not identify geometry defects from finite positive spans, does not select a profile, and does not change `FIELD_PROFILE_ID`, beta, theta, phase policy, translation policy, DG1, DG2, or any runtime path.
