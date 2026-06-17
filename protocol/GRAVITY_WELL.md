# GRAVITY_WELL Protocol

> Status: V1 protocol stub  
> Role: recall entry reference frame

---

## 1. Definition

A Gravity Well is created when recall begins.

It records the entry query, entry cell, chart, layer, and anchor vector.

It is not a boundary. It is the reference frame for measuring drift.

---

## 2. Minimal Schema

```yaml
gravity_well:
  well_id: gw_001
  entry_query: "..."
  chart_id: chart_alpha
  layer: 3
  q: 12
  r: -5
  anchor_vector:
    anchor_a: 0.91
    anchor_c: 0.44
  created_at: 2026-06-16T00:00:00+09:00
```

---

## 3. Non-Meanings

A Gravity Well is not:

```text
a folder
a parent node
an anchor owner
a hard recall boundary
a trust/status source
```

---

## 4. Projection Set Placeholder

R_column_ring depends on projecting the entry well to the content layer:

```text
Π_E(layer_C)
```

V1 projection set:

```text
Prefer coverage-template projection under the active geometry profile.
If unavailable, use nearest transformed center as approximate projection.
If neither is available, mark projection_method = unavailable.
```

Allowed projection_method values:

```text
coverage_template
approximate_center
unavailable
```

Projection is measurement only. It does not create children, ownership, or folders.
