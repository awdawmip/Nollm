# GRF1-A Validation Report

Implemented modules:

```text
reference/python/nollm/grf/axial.py
reference/python/nollm/grf/eisenstein.py
reference/python/nollm/grf/fixed_point.py
reference/python/nollm/grf/profiles.py
reference/python/nollm/grf/cell_address.py
reference/python/nollm/grf/coverage_template.py
reference/python/nollm/grf/kernel_store.py
reference/python/nollm/grf/validation.py
```

Implemented profiles:

```text
eisenstein_exact_v1 = production_candidate
aligned_baseline_v1 = baseline
dream_quasi_v1 = research
```

Weight format:

```text
q16_65536, Q16_ONE = 65536
```

Fanout:

```text
DEFAULT_FANOUT_LIMIT = 7
```

Runtime proof surface:

```text
exact profile runtime float count = 0 by source test
runtime polygon call count = 0 by source test
sin/cos call count = 0 by source test
coverage_up and coverage_down are distinct templates
dream_quasi_v1 is not the default performance profile
```

GRF1-B technical-debt closure:

```text
layer_index_direction = finer_with_increasing_index
coverage_up = fine to coarse, layer_delta = -1
coverage_down = coarse to fine, layer_delta = +1
normalization_residual_q16 is Q16 sum residual only
approximation_residual_q16 is compiler/profile approximation residual
dream_quasi_v1 uses approximation residual or boundary ambiguity, not normalization residual, to report approximation
```

Known non-goals:

```text
no EvidenceIsland persistence
no stitching workflow
no placement or admission migration
no recall product
no OpenClaw runtime activation
```

Failing-test intent:

```text
the tests are designed to fail if runtime code imports polygon tooling,
uses float conversion in exact lookup, selects dream_quasi as performance
default, reuses one direction for K up and K down, exceeds fanout, omits
residual reporting, accepts float q/r, or introduces object-level relation
language into GRF1-A runtime.
```

Next stage recommendation:

```text
GRF1-B should introduce EvidenceIsland and stitching semantics on top of this
integer/template kernel, without changing the GRF1-A runtime lookup contract.
```
