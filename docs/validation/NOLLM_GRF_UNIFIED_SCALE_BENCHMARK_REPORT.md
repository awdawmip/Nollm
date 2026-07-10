# NOLLM GRF Unified Scale Benchmark Report

Date: 2026-07-10

## Method

`experiments/grf/run_grf_unified_scale_validation.py` executes the cumulative
10K, 100K, 1M, and 10M milestones. Every generated item is a real
`EvidenceShardRecord` created through `GRFCaptureIngress`, a real
`PlacementRecord`, and a real `MinimalAdmissionRecord`. Every bounded partition
is inserted into `FieldEngine`, rebuilt as a `RelationField`, recalled through
`resolve_grf_recall`, and resolved back to its captured evidence source.

The validator retains at most 100,000 records at once. This is a partitioned
large-scale execution, not a claim that one monolithic in-memory
`RelationField` contains ten million placements. Partitioning bounds peak
memory while cumulative storage counters include every actual object and every
field partition.

Storage uses `getsizeof` on each real resident object and each actual field/index
container. Runtime uses `perf_counter_ns` around executed stages. No sampled
record is multiplied into a result, no formula metric replaces execution, and
no result is entered manually. Raw output is stored in
`experiments/grf/results/GRF_UNIFIED_SCALE_20260710.json`.

## Results

The complete run executed 101 field builds and 101 recalls.

| Objects | Partitions | Evidence bytes | Placement bytes | Admission bytes | Relation bytes | Index bytes | Kernel bytes | Fallback |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 10,000 | 1 | 5,748,890 | 15,082,250 | 3,868,890 | 4,105,840 | 1,565,744 | 1,913 | 10,000/10,000 |
| 100,000 | 2 | 57,588,890 | 151,422,250 | 38,788,890 | 54,786,144 | 19,591,016 | 1,913 | 100,000/100,000 |
| 1,000,000 | 11 | 576,888,890 | 1,520,222,250 | 388,888,890 | 533,876,880 | 192,006,464 | 1,913 | 1,000,000/1,000,000 |
| 10,000,000 | 101 | 5,778,888,890 | 15,262,222,250 | 3,898,888,890 | 5,324,784,240 | 1,916,160,944 | 1,913 | 10,000,000/10,000,000 |

| Objects | Capture ns | Placement ns | Admission ns | Rebuild ns | Recall ns | Update ns |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 10,000 | 178,796,000 | 238,822,400 | 48,317,400 | 106,448,100 | 4,646,200 | 30,400 |
| 100,000 | 1,754,508,800 | 2,520,473,100 | 415,121,700 | 1,651,884,100 | 54,085,400 | 64,500 |
| 1,000,000 | 17,298,688,700 | 24,718,061,800 | 4,137,553,700 | 15,950,199,800 | 581,435,300 | 269,900 |
| 10,000,000 | 163,441,714,600 | 236,325,312,800 | 40,372,009,800 | 154,396,466,900 | 5,629,598,600 | 2,349,300 |

Measured relation growth ratios are
`54786144/4105840`, `533876880/54786144`, and
`5324784240/533876880`. The validator's integer gate compares each measured
storage step with its measured input step and reports
`relation_growth_not_quadratic = true`. Maximum compiled template fanout is 6.
Kernel reuse reaches `10000000/14` and kernel storage remains 1,913 bytes at
all milestones.

## Gate

PASS.

- Real objects generated: 10,000,000.
- Source fallback preserved: 10,000,000/10,000,000.
- Relation growth is not quadratic: pass.
- Kernel size is independent of shard count: pass.
- Formula metrics, fake benchmark, and manual results: absent.
