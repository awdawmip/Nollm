# NOLLM GRF7 Cross-Partition Stitch Report

Gate C executes 103 proposals: 100 accepted sparse bridges, two false-friend
rejections, one rollback, and one decay classification. Accepted bridges are
used by recall. Rejected and rolled-back bridges are absent from later paths.
False-positive and missed-bridge rates are both 0/5000.

Fixtures cover source-backed relations, lexical false friends, wrong entities,
and rollback. No Evidence object or source reference is modified. Bridge
storage contains one record per accepted bridge, never object-pair expansion.

Raw: `experiments/grf/results/GRF7_CROSS_PARTITION_RECALL_RAW.json`.

`GATE_C_PASS`.
