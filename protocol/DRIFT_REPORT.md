# DRIFT_REPORT Protocol

> Status: V1 protocol stub  
> Role: computed recall-time drift annotation

---

## 1. Definition

A Drift Report is computed during recall by comparing a Gravity Well and a Gravity Mark.

It tells the model how far and how coherently the item has drifted from the entry well.

A Drift Report is instrumentation, not restriction.

---

## 2. Minimal Schema

```yaml
drift_report:
  well_id: gw_001
  content_id: shard_001
  R_column_ring: 4
  S_scale_delta: 2
  A_anchor_similarity: 0.82
  drift_class: far_coherent
  projection_method: coverage_template
  anchor_similarity_method: cosine_nonnegative_l2
  geometry_profile: default_dream
  P_path_decay: null
  X_chart_distance: null
  return_vector: null
```

---

## 3. A_anchor_similarity

For V1:

```text
A_anchor_similarity ∈ [0,1]
```

Meaning:

```text
0 = no meaningful anchor overlap
1 = identical normalized anchor vector
```

Method:

```text
cosine_nonnegative_l2
```

If signed cosine is used internally, normalize or clamp before writing the Drift Report.

---

## 4. Projection Method

Allowed values:

```text
coverage_template
approximate_center
unavailable
```

If projection_method is unavailable, R_column_ring may be null and drift_class should reflect chart/projection uncertainty.

---

## 5. Drift Class Labels

```text
core
halo
near_drift
far_coherent
far_weak
semantic_break
chart_jump
unglued
```

Precedence:

```text
1. unglued
2. chart_jump
3. semantic_break
4. core
5. halo
6. near_drift
7. far_coherent
8. far_weak
```

V1 rule:

```text
If A_anchor_similarity < 0.4, drift_class should be semantic_break,
unless chart status is unglued or chart_jump.
```

These thresholds change labels, not recall permissions.

---

## 6. Non-Meanings

A Drift Report must not:

```text
reject content
change trust/status
write memory
create parent/children
create anchor ownership
force return
```
