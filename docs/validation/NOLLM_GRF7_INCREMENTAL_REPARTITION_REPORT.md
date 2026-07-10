# NOLLM GRF7 Incremental Repartition Report

Gate F executes add, remove, local move, cross-partition move, profile change,
stitch add/remove, split, merge, directory refresh, and snapshot migration
semantics. Every operation changes measured state.

After migration, typed admission/placement recall matches an independently
constructed full rebuild. Evidence, Placement, and Admission identities remain
distinct and unchanged; fallback refs remain attached. Identity collisions are
zero and split/merge recall is stable.

Raw: `experiments/grf/results/GRF7_INCREMENTAL_RAW.json`.

`GATE_F_PASS`.
