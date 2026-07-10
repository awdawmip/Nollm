# NOLLM GRF5 Performance Evolution Report

For 100,000 placements and 1,000 shard-entry queries, the measured indexed
lookup took `733,500 ns`; the equivalent linear lookup took
`12,715,586,600 ns`. Results were identical. The entry index containers used
`19,328,448 bytes` as measured by `getsizeof`.

RelationField now builds shard, placement, island, patch, and source-window
indexes once with the immutable field snapshot. FieldEngine invalidates that
snapshot on placement or bridge mutation. Kernel/template caches and source
fallback semantics remain unchanged.

The operational 250-cycle run completed in `8,752,017,200 ns`; this is a local
file-first measurement, not a production network-service SLA.
