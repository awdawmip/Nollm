# Parameter Profiles

> Status: experimental registry protocol stub  
> Scope: geometry parameter profile identity and boundaries

## Definition

The parameter profile registry is deterministic. `profile_id` is the stable
reference key used by later geometry and gravity experiments.

Canonical profiles:

| profile_id | role | beta | theta_deg | tiling_model | orientation |
| --- | --- | --- | --- | --- | --- |
| `default_dream` | default | `2^(1/4)` | `22.5` | `T` | `pointy` |
| `medium_practical` | secondary | `sqrt(2)` | `15` | `T` | `pointy` |
| `benchmark_aligned` | benchmark | `2` | `0` | `T` | `pointy` |
| `benchmark_single_step` | benchmark | `2` | `15` | `T` | `pointy` |
| `benchmark_eisenstein` | benchmark | `sqrt(3)` | `30` | `T` | `pointy` |

`default_dream` is B: `2^(1/4)`, `22.5°`. B does not eliminate recurrence; it
delays recurrence.

`medium_practical` is A: `sqrt(2)`, `15°`. A remains secondary and practical,
not default.

Benchmarks are not defaults and must not be promoted because they are easy.

## Non-Meanings

The profile registry is not:

```text
a ranking engine
a recall controller
a trust/status mapper
a placement confirmation mechanism
a parent/children geometry model
```

Codex must not change defaults without explicit project-owner decision.
