# Nollm Project Specification V4 — Engineering Gravity Edition

> Date: 2026-06-16  
> Status: decision draft for implementation  
> Scope: engineering-oriented replacement for the previous metaphor-heavy gravity specification.  
> Rule: this document decides architecture; Codex only implements decided tasks.

---

## 1. Executive Definition

Nollm is a geometry-based memory topology layer for LLM recall.

It stores meaningful utterance-level shards in a rotating multi-scale honeycomb geometry. Recall begins from an entry Gravity Well, may drift freely, and attaches a Drift Report to every recalled item so the model knows how far and how coherently it has drifted.

Short motto:

```text
Let the model dream freely, but give every dream a compass.
```

Chinese:

```text
让模型自由做梦，但每个梦都带指南针。
```

Nollm is not a solved long-term memory system. It is an engineering hypothesis:

```text
Gravity reports help an LLM use recalled content better.
```

The next phase must test that hypothesis.

---

## 2. What Nollm Is / Is Not

### 2.1 What Nollm is

Nollm is:

```text
a memory topology layer on top of candidate retrieval.
```

The intended stack is:

```text
candidate retrieval layer
  vector search / HNSW / keyword / GraphRAG / other retriever
        ↓
Nollm topology layer
  geometry projection + drift instrumentation + return visibility
        ↓
LLM reasoning layer
  decide whether to use, continue drifting, return, or correct laterally
```

Nollm may receive candidates from a vector retriever or graph retriever, but its own contribution is not top-k retrieval. Its contribution is geometry marking and drift reporting.

### 2.2 What Nollm is not

Nollm is not:

```text
a vector database replacement
a GraphRAG clone
a folder/tag hierarchy
a normal knowledge graph
a pure visualization layer
a hard-gated recall controller
a solved long-term memory system
```

Nollm must not claim to solve long-term memory. It should claim only:

```text
a geometry-based memory organization and drift instrumentation mechanism
```

---

## 3. Core Engineering Hypothesis

The next engineering phase must test:

```text
Do gravity reports help an LLM use recalled content better?
```

Sub-hypotheses:

```text
H1: Gravity reports reduce misuse of far-drift content.
H2: Free drift reveals useful lateral associations missed by baseline retrieval.
H3: Return vectors help the model re-center when drift becomes weak or irrelevant.
H4: The default B profile is more stable than the A profile in finite-depth multi-step scan.
H5: The A profile is more robust under offset or gluing noise.
```

If H1 cannot be shown experimentally, Nollm risks becoming only a beautiful geometry metaphor.

---

## 4. Minimum Viable Data Model

V1 uses the smallest data model sufficient to test the hypothesis.

### 4.1 Dream Shard

A Dream Shard is an independently meaningful utterance-level unit.

```yaml
dream_shard:
  shard_id: shard_001
  text: "..."
  embedding: optional_external_reference_or_vector
  anchor_vector:
    anchor_a: 0.83
    anchor_b: 0.21
  created_at: 2026-06-16T00:00:00+09:00
  source_context: "conversation/document/source identifier"
  provenance:
    source_type: user_text | document | llm_output | imported
    source_id: "..."
  trust_level: unverified | llm-suggested | human-approved | source-backed | derived
  version_status: draft | candidate | confirmed | superseded | rejected | archived
```

Rules:

```text
1. Recall does not automatically create a Dream Shard.
2. A shard can be written only through explicit write flow.
3. llm_output shards cannot become confirmed without human/source-backed review.
```

### 4.2 Geometry Mark

A Geometry Mark records where a shard or candidate is projected in a geometry profile.

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

Rules:

```text
1. Geometry Mark is not ownership.
2. Geometry Mark is not parent-child relation.
3. Geometry Mark is not a folder or tag.
4. Geometry Mark may be approximate, but must expose its method.
```

### 4.3 Gravity Well

A Gravity Well is created at recall entry.

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

Rules:

```text
1. A Gravity Well is not a boundary.
2. A Gravity Well is a reference frame for measuring drift.
3. A Gravity Well does not own recalled content.
4. A Gravity Well does not force recalled content to remain nearby.
```

### 4.4 Gravity Mark

A Gravity Mark is the content-side location and anchor record used for drift computation.

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

A recall digest item may carry a copied or derived Gravity Mark for display and drift reporting. This does not make the digest item a new persistent memory object unless an explicit write operation creates it.

### 4.5 Drift Report

A Drift Report is computed during recall by comparing a Gravity Well and a Gravity Mark.

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

V1 required fields:

```text
well_id
content_id
R_column_ring
S_scale_delta
A_anchor_similarity
drift_class
projection_method
```

Future fields:

```text
P_path_decay
X_chart_distance
return_vector
```

Rules:

```text
1. Drift Report is instrumentation, not permission.
2. Drift Report must not map directly to trust/status.
3. Drift Report must not reject content.
4. Drift Report must not auto-write content.
5. A_anchor_similarity is normalized to [0,1] in V1.
```

### 4.6 Return Vector

Return Vector is optional in V1 experiments and required only when tested in the N3 ablation condition.

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

Rules:

```text
1. Return Vector is not a command.
2. Return Vector is a visible route home.
3. The LLM decides whether to return.
```

---

## 5. Geometry Decision

### 5.1 Main kernel: strict true tiling

The main geometry kernel must use Model T:

```text
Model T:
  true edge-to-edge regular hexagonal tiling
  center_spacing = √3 × side_length
```

Model O is optional research only. Model M is invalid and must be discarded.

### 5.2 Orientation conventions

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

Do not mix pointy-top centers with flat-top vertices.

### 5.3 Exact containment

Exact containment must use:

```text
target_share = Area(H_a ∩ H_b) / Area(H_b)
```

A target cell is exactly contained when:

```text
target_share = 1
```

Do not use `source_share` for exact containment.

### 5.4 Reverse-cover terminology

Only call a reverse-cover result `opt` if a real IP/MILP solver reports:

```text
OPTIMAL
```

Strict terms:

```text
greedy     = greedy cover result
incumbent  = best feasible solution found before timeout
opt        = proven optimum
gap        = (greedy - opt) / opt
```

---

## 6. Parameter Profile Registry

### 6.1 Default dream geometry

Use B as default:

```yaml
default_dream:
  beta: 2^(1/4)
  beta_float: 1.189207115002721
  theta_deg: 22.5
  role: default
```

B does not eliminate recurrence. B delays recurrence. For finite-depth scale scanning, delay is the useful property.

### 6.2 Secondary practical profile

Use A as secondary:

```yaml
medium_practical:
  beta: sqrt(2)
  beta_float: 1.4142135623730951
  theta_deg: 15
  role: secondary
```

A is retained for one-step spread, offset robustness, reverse-cover simplicity, and engineering comparison.

### 6.3 Benchmarks

```yaml
benchmark_aligned:
  beta: 2
  theta_deg: 0
  role: benchmark

benchmark_single_step:
  beta: 2
  theta_deg: 15
  role: benchmark

benchmark_eisenstein:
  beta: sqrt(3)
  theta_deg: 30
  role: benchmark
```

Do not promote benchmarks to default just because they are easy.

---

## 7. Recall Philosophy

### 7.1 Mode 3 free drift

Recall uses Mode 3 by default:

```text
Recall starts from an entry Gravity Well and may drift freely.
```

The system must not hard-limit lateral drift.

The LLM may decide:

```text
continue drifting
return to entry well
correct laterally
ignore a recalled item
use a far but coherent item
```

### 7.2 Gravity instrumentation

Gravity marking does not constrain recall. It annotates drift.

```text
R > 3 means mark as drift.
R > 3 does not mean reject.
```

### 7.3 Free drift is not auto-write

Free drift recall must not automatically become persistent memory.

Writing must pass:

```text
provenance
trust_level
version_status
conflict check
write permission
```

---

## 8. Drift Report Algorithm

### 8.1 Drift tuple

Use:

```text
G(E, C) = <R, S, A, P, X>
```

V1 implements only:

```text
R
S
A
drift_class
projection_method
```

### 8.2 R: column-ring drift

R is the minimum hex-ring distance from content cell C to the projection set of entry well E at C's layer:

```text
R = min_{p in Π_E(layer_C)} hex_distance(C, p)
```

V1 projection set:

```text
Prefer coverage-template projection under the active geometry profile.
If unavailable, use nearest transformed center as approximate projection.
Expose projection_method in the Drift Report.
```

Allowed projection methods:

```text
coverage_template
approximate_center
unavailable
```

### 8.3 S: scale delta

```text
S = abs(layer_C - layer_E)
```

### 8.4 A: anchor similarity

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

### 8.5 drift_class

Labels:

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
If A_anchor_similarity < 0.4, label semantic_break,
unless chart status is unglued or chart_jump.
```

These thresholds change labels, not permissions.

---

## 9. Minimal Algorithms

```text
write_shard
project_geometry_mark
create_gravity_well
generate_drift_report
create_digest
```

All five are experimental until evaluation shows value.

---

## 10. Evaluation Plan

The first experiment asks whether drift reports improve LLM use of recalled content.

Ablation matrix:

```text
N0: Vector RAG only
N1: Vector RAG + geometry mark only
N2: Vector RAG + gravity report
N3: Vector RAG + gravity report + return vector
N4: Nollm A profile: √2 / 15°
N5: Nollm B profile: 2^(1/4) / 22.5°
```

Success criteria:

```text
1. Gravity report reduces misuse of far-drift content.
2. Free drift finds useful lateral associations missed by baseline retrieval.
3. B profile is more stable than A in finite-depth multi-step scan.
4. A profile is more robust under offset/gluing noise.
5. Return vector improves the LLM's ability to re-center.
```

Failure criteria:

```text
1. Gravity report does not improve LLM judgment.
2. Drift report becomes unused decoration.
3. Geometry mark adds no value beyond embedding similarity.
4. Free drift mainly increases hallucination or irrelevant recall.
5. B profile's multi-step stability does not matter in actual recall tasks.
6. Implementation complexity exceeds measurable benefit.
```

---

## 11. Roadmap

```text
G0: decision documents
G1: strict true-tiling kernel hardening
G2: parameter profile registry
G3: multi-step coverage metrics
G4: offset sampling
G5: reverse-cover MILP
G6: gravity protocol implementation
G7: Mode 3 recall experiment
G8: full dream-field experiment
```

---

## 12. Non-goals and Warnings

Do not say Nollm solves long-term memory. Say Nollm provides a geometry-based memory organization and drift instrumentation mechanism.

Do not say B eliminates recurrence. Say B delays recurrence, which is useful for finite-depth scale scanning.

Do not say gravity mark controls recall. Say gravity mark annotates recall drift.

Do not say the hexagonal structure alone is the innovation. Say the contribution is the combination of dream shard, rotating multi-scale honeycomb, anti-tree parameter testing, Mode 3 free drift, and drift reporting.

Do not say recall result inside entry vertical projection is required. Say recall starts from an entry gravity well and may drift freely.

Do not let Codex change default geometry, turn gravity into a reject gate, map drift_class to trust/status, delete audit/history, create parent-child geometry, create stable public recall API before experiment, or auto-write drifted recall into memory.

---

## 13. Final Engineering Position

```text
Default geometry:
  β = 2^(1/4), θ = 22.5°

Secondary geometry:
  β = √2, θ = 15°

Recall:
  Mode 3 free drift by default

Control:
  gravity instrumentation, not hard restriction

First implementation:
  R/S/A/drift_class/projection_method only

First experiment:
  Does gravity report improve LLM use of recalled content?

Main engineering test:
  If gravity report does not improve recall judgment,
  Nollm remains only a beautiful geometry metaphor.
```

One sentence:

```text
Do not build a bigger metaphor; build the smallest experiment that can prove whether the compass helps.
```
