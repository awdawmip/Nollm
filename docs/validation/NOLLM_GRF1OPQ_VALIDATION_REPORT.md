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
