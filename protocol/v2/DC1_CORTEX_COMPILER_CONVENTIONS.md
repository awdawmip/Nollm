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
