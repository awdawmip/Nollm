# GEO1 Geometry Evidence Consolidation Protocol

GEO1 consolidates sealed finite geometry evidence into an audit ledger and a production-freeze decision.

## Source Policy

The runner uses a fixed nine-phase whitelist. It reads each listed report, scope, and protocol path directly and records SHA-256 digests for deterministic verification. It performs no repository scan, automatic experiment discovery, semantic clustering, ranking, or model-based summarization.

## Ledger Policy

Each finding has fixed structured fields:

- `finding_id`
- `status`
- `source_phase_ids`
- `verified_statement`
- `non_inference`
- `production_effect`
- `open_question`

The ledger distinguishes finite verified statements from non-inferences and open questions. It is an audit consolidation, not a new geometry source of truth.

## Freeze Policy

The production freeze decision may only produce `HOLD` and `OPEN` outcomes. GEO1 cannot recommend replacing beta, 22.5 degree rotation, phase policy, coverage direction, `FIELD_PROFILE_ID`, or any production geometry behavior.
