# NOLLM GRF7 Resource Accounting Report

Gate E keeps units and structures separate.

| Structure | RSS peak bytes | tracemalloc peak bytes | deep estimate bytes | shallow estimate bytes |
| --- | ---: | ---: | ---: | ---: |
| 1M resident field | 7,663,575,040 | 3,292,602,337 | 2,845,839,662 | 144,000,000 |
| 10M global-sharded stage | 1,108,865,024 | 488,788,271 | 23,530,000,030 cumulative | 1,440,000,000 cumulative |

The global artifact contains 303 scale files, 1,108,815,036 serialized disk
bytes from 1,360,000,000 uncompressed row bytes, and reloads 10M placement
rows in 33,692,071,100 ns. Directory bytes are 108,747. Kernel storage remains
400 bytes in the scale schema and is independent of shard count.

All final external runtime/long-run/scale artifacts total 1,234,890,259 bytes
across 310 files. Every file has a committed SHA-256 entry in
`GRF7_EXTERNAL_ARTIFACT_HASHES.json`; post-move verification found zero
mismatches.

An initial combined-process run inherited the resident Windows RSS peak in its
global field. That global measurement was rejected and rerun in a global-only
process scope. The superseded bytes are retained outside the final manifest at
`C:\Users\chaos\nollm_grf7_superseded_global_evidence_20260710`.

`GATE_E_PASS`.
