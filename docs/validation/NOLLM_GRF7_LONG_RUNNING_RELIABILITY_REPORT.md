# NOLLM GRF7 Long-Running Reliability Report

Gate H uses the permitted fixed-work substitute and executes 1,000,000
operations without sleep. Twelve operation classes each run about 83,333
times. There are 83,333 injected adapter failures and 83,333 recoveries, ten
resource checkpoints, zero orphan references, zero Evidence loss, zero identity
collisions, and deterministic final replay.

Average latency rises from 609,591 to 4,193,771 ns/operation. The drift is
recorded rather than hidden; it follows growing per-partition occupancy plus
periodic split/merge and failure recovery. Peak RSS is 940,843,008 bytes and
tracemalloc peak is 412,923,918 bytes.

Raw: `experiments/grf/results/GRF7_LONG_RUNNING_RAW.json`.

`GATE_H_PASS`.
