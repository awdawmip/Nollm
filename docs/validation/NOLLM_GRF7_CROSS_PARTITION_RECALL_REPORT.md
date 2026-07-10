# NOLLM GRF7 Cross-Partition Recall Report

Gate B executes 1K, 5K, 10K, and 20K query workloads against the accepted
resident/global scale shapes. The 10M workload includes 5,000 real boundary
crossings, 1,000 stitch queries, and 1,000 rollback/rejection queries.

All 20,000 exact identity queries return the entry shard, all 20,000 executed
recalls preserve fallback, and every path records its entry/visited partitions,
crossing, kernel, bridge, activation count, and fallback. Maximum observed
partition hops and fanout are one; maximum loaded partitions are two. Replay
is deterministic and no all-partition scan occurs.

Raw: `experiments/grf/results/GRF7_CROSS_PARTITION_RECALL_RAW.json`.

`GATE_B_PASS`.
