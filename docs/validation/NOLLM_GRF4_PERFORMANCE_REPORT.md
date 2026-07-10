# NOLLM GRF4 Performance Report

The production-like runner processed 1,000,001 actual synthetic evidence and
placement records using three profiles: `eisenstein_exact_v1`,
`dream_quasi_v1`, and `aligned_baseline_v1`.

| Measurement | Result |
| --- | ---: |
| Continuous capture and FieldEngine insertion | 41,701,629,200 ns |
| Field rebuild | 3,243,020,000 ns |
| Recall | 260,147,600 ns |
| First coverage-template load | 221,300 ns |
| Cached coverage-template load | 700 ns |
| Measured engine memory structures | 221,245,664 bytes |
| Throughput expression | 1,000,001 / 41,701,629,200 items/ns |

Field snapshots cache immutable relation fields. An insert, remove, move, or
bridge update invalidates that cache, and the next build constructs a fresh
snapshot. The runner compared a moved-placement incremental snapshot against
an independently rebuilt field and obtained equality.

GATE_D_PASS and GATE_E_PASS. These are local deterministic Python prototype
measurements, not a claim of a deployed terminal service throughput.
