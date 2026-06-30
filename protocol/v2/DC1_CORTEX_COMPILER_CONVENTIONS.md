# DC1 Cortex Compiler Conventions

- `gp_...` identifies compiled Growth Proposals.
- `probe_...` identifies ephemeral Query Probes.
- `cr_...` identifies Compilation Receipts.
- `step_...` identifies ray steps.
- `rule_...` identifies caller-declared rule references.

Allowed reserved axes are `location`, `phenomenon`, `absolute_time`,
`relative_time`, `source`, `constraint`, `revision`, and `relation`.
Custom axes use `custom/<lowercase-kebab-or-snake-name>`.

Growth steps may use `explicit_in_shard`, `deterministic_projection`,
`backed_by_other_shard`, `source_backed_rule`, or
`provisional_llm_generalization`.

Query steps may use `explicit_in_query`, `deterministic_projection`,
`source_backed_rule`, or `provisional_llm_generalization`.

`explicit_in_shard`, `explicit_in_query`, and `backed_by_other_shard` require
exact Unicode character spans. DC1 performs no fuzzy matching, tokenization,
synonym repair, or time resolution.

Growth submissions use:

```yaml
budget:
  max_axes: 8
  max_total_steps: 48
  max_ray_steps: 16
possible_conflict_refs: []
```

Query submissions use:

```yaml
budget:
  max_axes: 8
  max_charts: 64
  max_layers: 64
  max_cells_per_layer: 256
```

Old Query budget keys such as `max_total_steps` and `max_ray_steps` are not
accepted for Query Probes.
