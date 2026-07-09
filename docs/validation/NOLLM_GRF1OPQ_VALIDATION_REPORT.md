# NOLLM GRF1-OPQ Validation Report

## Gate O

GATE_O_PASSED

- GRFPlacementPolicy implemented.
- Default facade admission uses grf_deterministic_policy_v1.
- validation_fixture_policy remains only as explicit compatibility mode.
- Candidate generation is bounded and deterministic.
- Ranking uses Q16/int arithmetic.
- No embedding/global search/semantic edge path.
- Defer/reject outcomes are represented and preserve evidence.
- PlacementRankingReport explains selected cell.

## Gate P

GATE_P_PASSED

- Public GRFFacade recall supports explicit_cell/shard_id/island_id/patch_id/source_window/admission_id/placement_id.
- All entry modes resolve without global search.
- Seeded recall generalization runs at least 20 seeds.
- Replay equality holds.
- Selected shards all resolve source fallback.
- CLI remains single-JSON envelope and safe error surface.
