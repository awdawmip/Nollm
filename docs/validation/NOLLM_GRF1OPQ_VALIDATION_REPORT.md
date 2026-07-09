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

## Gate Q

GATE_Q_PASSED

- Scale validation >= 5000 items.
- Deterministic placement policy variant evaluated.
- Query generalization variant evaluated.
- Relation storage remains below explicit graph baseline.
- Runtime no polygon/no exact float preserved.
- Failure/limitation cases reported honestly.
- No graph/vector/embedding main path introduced.

Failure and limitation cases recorded:

- false-friend high lexical overlap;
- sparse evidence insufficient source affinity;
- over-dense cell causing defer;
- ambiguous patch boundary;
- bridge candidate rejected;
- source fallback missing simulated warning;
- explicit graph baseline beats GRF on a narrow fixture;
- GRF relation storage advantage but lower recall correctness case.
