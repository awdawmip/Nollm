# GRF Profile

GRF V3 profiles define how integer cell addresses and offline coverage
templates are interpreted. GRF1-A defines three profiles only:

```text
eisenstein_exact_v1   role = production_candidate
aligned_baseline_v1   role = baseline
dream_quasi_v1        role = research
```

All GRF1-A profiles use:

```text
coordinate_model = integer_axial_cube
weight_format = q16_65536
runtime_polygon = false
```

`eisenstein_exact_v1` is the first performance main candidate. It uses
Eisenstein integer transforms and fixed-point weights. Runtime lookup for this
profile must not use float arithmetic, trigonometry, polygon overlap, semantic
search, or graph traversal.

`aligned_baseline_v1` is a control profile. It exists to keep exact integer
behavior testable without scale or rotation transforms.

`dream_quasi_v1` is a research profile. It can publish symbolic residual and
boundary ambiguity, but it is not the default performance profile.
