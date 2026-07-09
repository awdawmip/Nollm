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
