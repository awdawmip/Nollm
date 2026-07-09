# GRF Coverage Kernel

GRF1-A coverage is an offline compiled template relation. Runtime code performs
bounded template lookup and integer address expansion.

Template entry:

```text
KernelEntry(layer_delta, dq, dr, weight_q16, kernel_type, flags)
```

Template:

```text
CoverageTemplate(
  profile_id,
  direction,
  from_layer_mod,
  to_layer_mod,
  source_phase,
  entries,
  sum_weight_q16,
  residual_q16,
  compiler
)
```

Directions:

```text
coverage_up
coverage_down
lateral
```

Layer convention:

```text
layer_index_direction = finer_with_increasing_index
layer 0 = coarser
layer 1,2,3... = progressively finer
coverage_up = fine to coarse, layer_delta = -1
coverage_down = coarse to fine, layer_delta = +1
```

`coverage_up` and `coverage_down` are separate normalized semantics. GRF1-A
does not define them as the same object, and does not claim that one is a
simple transpose of the other.

Runtime requirements:

```text
no float scoring for exact profile
no sin/cos
no polygon overlap
no geometry clipping
fanout <= hard bound
deterministic ordering
```

GRF1-A uses `q16_65536`, where `Q16_ONE = 65536`.

Residual fields:

```text
normalization_residual_q16 = Q16_ONE - sum(entry.weight_q16)
approximation_residual_q16 = profile/compiler approximation residual
```

Exact and aligned profiles use `approximation_residual_q16 = 0`. Research
templates such as `dream_quasi_v1` may report non-zero approximation residual
or boundary ambiguity while keeping normalization residual separate.
