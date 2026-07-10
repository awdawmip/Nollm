# NOLLM GRF7 Scale Report

Gate D builds resident fields of 100K, 500K, and 1M placements in one
`FieldEngine`. Each milestone builds a `RelationField`, executes recall, and
preserves fallback for every generated placement. The 1M resident field has
50,000 occupied cells and fallback 1,000,000/1,000,000.

The global run generates 10,000,000 Evidence/Placement/Admission chains across
100 independently built 100K partitions. It executes 100 field builds and 100
partition recalls, writes all partition stores, then reloads exactly 10M
placement rows. The final global directory has 99 bridge records and 198
directed neighbor links. Loaded partition count after build is zero; query
workloads load at most two. This is not a resident 10M field.

Raw: `experiments/grf/results/GRF7_SCALE_RAW.json`.

`GATE_D_PASS`.
