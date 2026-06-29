# V2 Object Ownership

Object sovereignty is module-owned:

- `dream_shard`: evidence, durable, externally visible.
- `ledger_event`: evidence, durable, externally visible.
- `growth_proposal`: cortex.
- `query_probe`: cortex, not durable.
- `local_chart`: geometry.
- `chart_transform`: geometry.
- `coverage_kernel`: geometry, not externally visible in DG0.
- `growth_trace`: field.
- `coarse_cover`: field.
- `gravity_snapshot`: field, internal only.
- `trace_compaction`: field, derived view, internal only.
- `recall_digest`: recall.

Evidence, Trace, and Cover are not interchangeable. Trace and Cover never erase or replace Evidence.
Gravity and compaction are internal Field views. They never authorize external query parameters, anchors, ledger writes, or replacement of original Evidence / Trace inputs.
