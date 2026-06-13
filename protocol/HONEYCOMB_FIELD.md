# Honeycomb Field

Layered rotating honeycomb memory field.

Each layer consists of equal-sized regular hexagonal cards. Cards exist at every scale. There is no absolute leaf layer.

Next layer total card density = previous layer density × √2.

Layer `l` rotation:

`θ_l = (l × 22.5°) mod 60°`

All layers share pole `O`.

`O` is a shared vertex of the three central hex cards in every layer.

`O` is not root, not directory, not entry point.

No strict parent-child containment.

No absolute leaf layer.

## Formulas

```text
D_l = D_0 × (√2)^l
A_l = A_0 × 2^(-l/2)
s_l = s_0 × 2^(-l/4)
θ_l = (l × 22.5°) mod 60°
```

## Runtime Status

The current reference runtime remains filesystem-first and deterministic.

P5.4 preserves and validates optional card metadata:

- `layer` as a non-negative integer.
- `hex.q` and `hex.r` as required integer coordinates when `hex` is present.
- `hex.rotation` as numeric metadata matching `(layer * 22.5) mod 60`.
- `hex.scale` as positive numeric metadata matching `2 ** (-layer / 4)`.

Core does not implement geometric runtime behavior, visualization, automatic coordinate placement, or polygon overlap calculation.
