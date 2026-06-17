# Nollm Minimum Data Model V4

> Date: 2026-06-16  
> Status: engineering starting point  
> Purpose: smallest schema sufficient to test gravity reports.

---

## 1. Design Rule

Keep the data model small enough to implement, test, and falsify.

V1 implements:

```text
DreamShard
GeometryMark
GravityWell
GravityMark
DriftReport
ReturnVector placeholder
```

V1 must not implement:

```text
automatic persistent writeback from recall
stable public recall tool surface
trust/status mapping from drift class
anchor ownership
parent/children geometry
```

---

## 2. DreamShard

```yaml
dream_shard:
  shard_id: shard_001
  text: "..."
  embedding: optional_external_reference_or_vector
  anchor_vector:
    anchor_a: 0.83
    anchor_b: 0.21
  created_at: 2026-06-16T00:00:00+09:00
  source_context: "..."
  provenance:
    source_type: user_text | document | llm_output | imported
    source_id: "..."
  trust_level: unverified | llm-suggested | human-approved | source-backed | derived
  version_status: draft | candidate | confirmed | superseded | rejected | archived
```

Validation:

```text
shard_id required
text non-empty
anchor_vector nonnegative for V1
trust_level enum
version_status enum
```

---

## 3. GeometryMark

```yaml
geometry_mark:
  content_id: shard_001
  profile: default_dream
  beta: 1.189207115002721
  theta_deg: 22.5
  chart_id: chart_alpha
  layer: 3
  q: 12
  r: -5
  world_center:
    x: 183.42
    y: -71.80
  side_length: 0.7071067812
  rotation_deg: 67.5
  projection_method: assigned | experimental | imported | approximate
```

Non-meaning:

```text
GeometryMark is not ownership.
GeometryMark is not parent-child.
GeometryMark is not folder/tag.
```

---

## 4. GravityWell

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

Non-meaning:

```text
GravityWell is not boundary.
GravityWell is not owner.
GravityWell is not folder.
GravityWell is only reference frame for drift.
```

---

## 5. GravityMark

```yaml
gravity_mark:
  content_id: shard_001
  chart_id: chart_alpha
  layer: 5
  q: 31
  r: -18
  geometry_profile: default_dream
  anchor_vector:
    anchor_a: 0.62
    anchor_d: 0.88
  provenance:
    mark_source: geometry_projection | imported | experiment
```

A recall digest item may carry a copied or derived GravityMark. This does not make the digest item persistent memory.

---

## 6. DriftReport

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

Validation:

```text
R_column_ring integer >= 0 unless projection_method = unavailable
S_scale_delta integer >= 0
A_anchor_similarity numeric in [0,1]
projection_method enum: coverage_template | approximate_center | unavailable
anchor_similarity_method enum: cosine_nonnegative_l2
drift_class enum
```

---

## 7. Drift Class Precedence

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
If A_anchor_similarity < 0.4, use semantic_break,
unless chart status is unglued or chart_jump.
```

Labels are not permissions.

---

## 8. ReturnVector

```yaml
return_vector:
  nearest_projection_layer: 5
  nearest_projection_cell:
    q: 18
    r: -9
  ring_distance: 4
  suggested_anchor_back:
    - anchor_a
    - anchor_c
```

V1 may store null.

ReturnVector is not a command. It is route visibility.

---

## 9. Explicit Anti-Auto-Write Rule

```text
free drift recall ≠ automatic memory write
```

Persistent write requires:

```text
provenance
trust_level
version_status
conflict check
write permission
```
