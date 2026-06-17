# Nollm Parameter Profile Registry

G2 adds a deterministic registry for geometry parameter profiles so later G3-G8
tasks can refer to `profile_id` instead of retyping beta/theta constants.

All canonical G2 profiles use strict true tiling Model T and pointy orientation.

| profile_id | role | beta | theta_deg | purpose |
| --- | --- | --- | --- | --- |
| `default_dream` | default | `2^(1/4)` | `22.5` | B profile; slow densification; delays finite-depth recurrence |
| `medium_practical` | secondary | `sqrt(2)` | `15` | A profile; practical comparison and offset robustness |
| `benchmark_aligned` | benchmark | `2` | `0` | aligned hidden-tree benchmark |
| `benchmark_single_step` | benchmark | `2` | `15` | one-step anti-tree benchmark |
| `benchmark_eisenstein` | benchmark | `sqrt(3)` | `30` | hex/Eisenstein benchmark |

Later geometry and gravity tasks should store or report the stable `profile_id`.
They may derive `LayerSpec` values from the registry, but the registry itself
does not compute multi-step metrics, run offset sampling, perform recall, or
rank profiles.

Warning: B delays recurrence. It does not eliminate recurrence. Benchmarks are
diagnostic profiles, not candidates for silent default promotion.
