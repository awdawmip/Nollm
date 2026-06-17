# Nollm True-Tiling Engineering Requirements

> Date: 2026-06-16  
> Status: geometry engineering requirements  
> Purpose: prevent geometry convention errors before gravity experiments.

---

## 1. Main Rule

The main geometry kernel must use Model T:

```text
true edge-to-edge regular hexagonal tiling
center_spacing = √3 × side_length
```

Model O is research-only. Model M is invalid and must be rejected.

---

## 2. Model Definitions

```text
Model T:
  true edge-to-edge regular hexagonal tiling
  center_spacing = √3 × side_length

Model O:
  overlapping hexagonal influence field
  center_spacing = side_length
  average multiplicity = 3

Model M:
  invalid mixed convention
  pointy-top center formula + flat-top vertices
```

Do not import Model O facts into Model T.

---

## 3. Orientation Conventions

Pointy-top true tiling:

```text
centers:
  x = √3 s (q + r/2)
  y = 3s r / 2

vertices:
  angle = rotation + 30° + 60°j
```

Flat-top true tiling:

```text
centers:
  x = 3s q / 2
  y = √3 s (r + q/2)

vertices:
  angle = rotation + 60°j
```

Forbidden:

```text
pointy-top centers + flat-top vertices
flat-top centers + pointy-top vertices
```

---

## 4. Coverage Metrics

```text
source_share = Area(H_a ∩ H_b) / Area(H_a)
target_share = Area(H_a ∩ H_b) / Area(H_b)
```

Use target_share for exact containment.

Exact containment:

```text
target_share = 1
```

Do not use source_share for exact containment.

---

## 5. Parameter Profiles To Test

```text
B default:      β = 2^(1/4), θ = 22.5°
A secondary:   β = √2,      θ = 15°
Benchmarks:    β = 2, θ = 0°; β = 2, θ = 15°; β = √3, θ = 30°
```

---

## 6. Required Tests

```text
pointy center + pointy vertices: valid
flat center + flat vertices: valid
mixed convention: rejected
center spacing = √3s
coverage source_share one-step sums close to 1
target_share exact containment test
A/B one-step template smoke test
n=1..8 multi-step metric smoke test
```

---

## 7. Reverse-Cover Terms

```text
greedy     = greedy cover result
incumbent  = best feasible solution found before timeout
opt        = proven optimum
gap        = (greedy - opt) / opt
```

Only use opt if solver status is:

```text
OPTIMAL
```

---

## 8. G1 Implementation Status

```text
pointy-top true tiling: implemented and tested
flat-top true tiling: implemented and tested
Coverage.source_share / target_share aliases: implemented
exact containment: tested with target_share
Model O center_spacing = side_length: guarded against in tests
Model M mixed center/vertex convention: guarded against in tests
A/B one-step strict Model T templates: tested
```
