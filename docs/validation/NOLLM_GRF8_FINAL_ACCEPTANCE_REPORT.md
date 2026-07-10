# GRF8 Final Acceptance

## Verified

- Gate 0: independent Windows snapshot restore and sustained-workload replay.
- Gate A/B: six source types, lossless source fallback, idempotent ingestion,
  explicit batch placement and admission.
- Gate D/E: deterministic six-category dataset with 10,000 evidence items and
  1,000 ground-truth queries; ranking metrics are computed from query results.
- Gate F/G: 600 workflow queries and File, Codex, OpenClaw lifecycle fixtures.
- Gate H: 1,000,000 operations completed with zero orphans and replay true.
- Gate I: measured full ingest, unchanged incremental reload, batch placement,
  and snapshot restore paths without losing source fallback.

## Windows Results

`reference/python/tests/grf`: 183 passed.

Architecture, forbidden-feature, and repository-hygiene checks: 7 passed.

## Limits

The dataset and hosts are deterministic fixtures. This stage does not claim a
production SLA, external-dataset generalization, live Host deployment, or
Linux/macOS validation. GRF8_ACCEPTED_CANDIDATE applies only to the stated
Windows validation scope.
