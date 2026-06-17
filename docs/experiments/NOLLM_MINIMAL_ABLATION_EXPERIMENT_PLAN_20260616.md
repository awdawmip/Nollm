# Nollm Minimal Ablation Experiment Plan

> Date: 2026-06-16  
> Status: experimental plan  
> Goal: test whether gravity reports improve LLM use of recalled content.

---

## 1. Engineering Hypothesis

```text
Gravity reports help an LLM use recalled content better.
```

Specifically, they should:

```text
1. reduce misuse of far-drift content;
2. make lateral discoveries visible;
3. help the model decide whether to continue drifting, return, or correct laterally.
```

If this cannot be shown, Nollm should be reconsidered.

---

## 2. Prototype Pipeline

```text
1. Input dream shards.
2. Generate embedding and anchor_vector.
3. Retrieve candidates using existing retrieval layer.
4. Project candidates into Nollm geometry marks.
5. Create query gravity well.
6. Generate R/S/A/drift_class for each candidate.
7. Show candidates to LLM with and without gravity reports.
8. Compare outputs.
```

Nollm does not replace the candidate retrieval layer. It instruments candidates after retrieval.

---

## 3. Ablation Conditions

```text
N0: Vector RAG only
N1: Vector RAG + geometry mark only
N2: Vector RAG + gravity report
N3: Vector RAG + gravity report + return vector
N4: Nollm A profile: √2 / 15°
N5: Nollm B profile: 2^(1/4) / 22.5°
```

Recommended first comparison:

```text
N0 vs N2: Does gravity report help at all?
N2 vs N3: Does return vector help re-centering?
N4 vs N5: Does default B provide better finite-depth stability than A?
```

---

## 4. Dataset Shape

Minimum first dataset:

```text
20-50 short source documents
100-300 dream shards
10-30 questions
known relevant and distractor items
some far-but-useful lateral items
some far-and-bad misleading items
```

Each question should have:

```text
entry query
expected core evidence
expected lateral evidence if any
known distractors
answer rubric
```

---

## 5. Metrics

Generic:

```text
answer correctness
faithfulness / provenance correctness
recall@k
MRR
latency
token cost
```

Nollm-specific:

```text
drift_visibility_gain
useful_lateral_discovery
over_drift_rate
return_vector_usage
anti_tree_stability
```

---

## 6. Required Reports

Each run should produce deterministic JSON:

```yaml
run_id:
condition:
profile:
question_count:
candidate_count:
drift_class_distribution:
metrics:
  answer_correctness:
  faithfulness:
  drift_visibility_gain:
  useful_lateral_discovery:
  over_drift_rate:
  return_vector_usage:
  latency:
  token_cost:
failures:
  - question_id:
    failure_type:
    notes:
```

Also produce Markdown triage:

```text
what improved
what worsened
what failed
whether gravity report was used or ignored
next changes
```

---

## 7. Success Criteria

Continue if:

```text
1. Gravity report reduces misuse of far-drift content.
2. Free drift finds useful lateral associations missed by baseline retrieval.
3. B profile is more stable than A in finite-depth multi-step scan.
4. A profile is more robust under offset/gluing noise.
5. Return vector improves re-centering.
```

---

## 8. Failure Criteria

Reconsider if:

```text
1. Gravity report does not improve LLM judgment.
2. Drift report becomes unused decoration.
3. Geometry mark adds no value beyond embedding similarity.
4. Free drift mainly increases hallucination or irrelevant recall.
5. B profile's multi-step stability does not matter in actual recall tasks.
6. Implementation complexity exceeds measurable benefit.
```
