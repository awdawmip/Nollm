# V2 Object Ownership

Object sovereignty is module-owned:

- `dream_shard`: evidence, durable, externally visible.
- `interpretation_record`: evidence, durable, externally visible.
- `revision_thread`: evidence, durable, externally visible.
- `usage_state_transition`: evidence, durable, externally visible.
- `ledger_event`: evidence, durable, externally visible.
- `compiled_growth_proposal`: cortex, durable only within the Cortex compiler store.
- `compilation_receipt`: cortex, durable only within the Cortex compiler store.
- `query_probe`: cortex, not durable.
- `local_chart`: geometry.
- `chart_transform`: geometry.
- `coverage_kernel`: geometry, not externally visible in DG0.
- `growth_trace`: field.
- `coarse_cover`: field.
- `gravity_snapshot`: field, internal only.
- `trace_compaction`: field, derived view, internal only.
- `recall_digest`: recall, not durable, externally visible as an ephemeral read result.
- `recall_universe`: recall call boundary, finite and explicit, not durable.
- `runtime_time_resolution`: recall call boundary, caller-supplied relative-time resolution, not durable.
- `validated_recall_universe`: recall-local validation view, not durable.

Evidence, Trace, and Cover are not interchangeable. Trace and Cover never erase or replace Evidence.
Gravity and compaction are internal Field views. They never authorize external query parameters, anchors, ledger writes, or replacement of original Evidence / Trace inputs.

DE1 Evidence records original memory material and epistemic state. Interpretation,
revision, and usage-state records do not overwrite DreamShard content and do not
claim truth, authentication, or Field placement.

DR1 Recall records only ephemeral digests. It may qualify evidence and report
coverage residuals, but it never owns DreamShard content, proposal content, field
state, geometry rules, gravity state, adapter state, runtime history, query
history, or traversal history. `RuntimeTimeResolution` and
`ValidatedRecallUniverse` are call-local views only.
