# Nollm Engineering Roadmap V4

> Date: 2026-06-16  
> Status: implementation roadmap  
> Principle: implement, test, falsify, ablate, iterate.

---

## 0. Roadmap Rule

The project now moves from metaphor expansion to engineering verification.

Every milestone must answer:

```text
What can be implemented?
What can be tested?
What can fail?
What can be ablated?
What result would make us change direction?
```

Codex must not decide architecture. Codex only implements decided tasks.

---

## W2 - OpenClaw Direct Active Memory Trial

Owner-authorized empirical cutover of the OpenClaw memory slot to the `nollm` native active memory provider.

Deliver:

- `integrations/openclaw/nollm-memory-provider/` as active memory-slot owner.
- `agent_turn_prepare` recall from the W1 native companion store into a bounded `NOLLM_MEMORY_CONTEXT_V1` envelope.
- `agent_end` deterministic explicit stable-sentence capture into the same native store.
- Local-only redacted trial metrics and a tested rollback path.
- No Primary-visible Nollm memory tools in active mode.
- No read/write of `MEMORY.md`, `DREAMS.md`, or `memory/*.md`.

Acceptance:

- `plugins.slots.memory` resolves to `nollm`.
- Real Gateway restart/reload succeeds with `nollm` loaded.
- Synthetic identity/preference/release markers are captured and recalled across real turns.
- Duplicate statements deduplicate; secret-like statements are rejected.
- Legacy source hashes are preserved; rollback to `memory-core` is proven.
- Workspace `MEMORY.md` bootstrap is recorded as a measured confound, not a blocker or silent assumption.

## G0 — Engineering Decision Documents

Deliver:

```text
NOLLM_PROJECT_SPEC_V4_ENGINEERING_GRAVITY_20260616.md
docs/roadmap/NOLLM_ENGINEERING_ROADMAP_V4_20260616.md
docs/engineering/NOLLM_MINIMUM_DATA_MODEL_20260616.md
docs/experiments/NOLLM_MINIMAL_ABLATION_EXPERIMENT_PLAN_20260616.md
docs/geometry/NOLLM_TRUE_TILING_ENGINEERING_REQUIREMENTS_20260616.md
protocol/GRAVITY_WELL.md
protocol/GRAVITY_MARK.md
protocol/DRIFT_REPORT.md
protocol/RETURN_VECTOR.md
```

Acceptance:

```text
Docs state Nollm as memory topology layer on top of candidate retrieval.
Docs state Mode 3 free drift.
Docs state gravity instrumentation is not hard restriction.
Docs include success and failure criteria.
Docs forbid automatic writeback from recall.
```

---

## G1 — Strict True-Tiling Kernel Hardening

Implement and test:

```text
pointy-top true-tiling centers
pointy-top true-tiling vertices
flat-top true-tiling centers
flat-top true-tiling vertices
center_spacing = √3s
coverage source_share checks
target_share exact containment checks
mixed-convention regression tests
```

Acceptance:

```text
No true-tiling test may import Model O multiplicity=3 as Model T.
No exact containment test may use source_share.
No reverse-cover timeout result may be named opt.
```

---

## G2 — Parameter Profile Registry

Implement registry:

```yaml
default_dream:
  beta: 2^(1/4)
  theta_deg: 22.5
  role: default

medium_practical:
  beta: sqrt(2)
  theta_deg: 15
  role: secondary

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

Acceptance:

```text
No code path silently promotes benchmark profile to default.
```

---

## G3 — Multi-Step Coverage Metrics

Implement:

```text
n=1..8 coverage templates
coverage_count
PR
entropy
exact_containment_count
boundary_ambiguity_count
critical beta threshold scan
```

Required comparison:

```text
A = sqrt(2) / 15°
B = 2^(1/4) / 22.5°
benchmarks = 2/0°, 2/15°, sqrt(3)/30°
```

Acceptance:

```text
Reports must say B delays recurrence, not eliminates recurrence.
Reports must not reduce anti-tree quality to one-step PR.
```

---

## G4 — Offset Sampling

Implement:

```text
deterministic offsets
random offsets
fixed seeds
variance metrics
A/B comparison
```

Acceptance:

```text
Offset reports identify A as practical/offset-robust if metrics show it.
Offset reports do not override B as default dream geometry.
```

---

## G5 — Reverse-Cover MILP

Implement:

```text
greedy cover
MILP/IP exact solver if available
LP lower bound
capacity lower bound
component lower bound
diameter lower bound
strict solver status
timeout incumbent handling
```

Acceptance:

```text
Use opt only when solver status is OPTIMAL.
Use incumbent for feasible timeout result.
Report gap only against proven opt.
```

---

## G6 — Gravity Protocol Implementation

Implement:

```text
GravityWell
GravityMark
DriftReport
ReturnVector placeholder
A_anchor_similarity in [0,1]
projection_method enum
drift_class precedence
R_column_ring
S_scale_delta
```

Acceptance:

```text
Gravity Report is annotation, not rejection.
Drift class does not map to trust/status.
Free drift recall does not auto-write memory.
```

---

## G7 — Mode 3 Recall Experiment

Experiment only:

```text
input shards
candidate retrieval adapter
geometry projection
gravity well creation
drift report generation
digest with drift metadata
LLM prompt variants with/without gravity report
```

Acceptance:

```text
No stable public recall/tool surface.
No hard drift cutoff.
No automatic writeback.
Digest includes drift class distribution.
```

---

## G8 — Full Dream-Field Experiment

Conditions:

```text
N0: Vector RAG only
N1: Vector RAG + geometry mark only
N2: Vector RAG + gravity report
N3: Vector RAG + gravity report + return vector
N4: A profile sqrt(2)/15°
N5: B profile 2^(1/4)/22.5°
```

Metrics:

```text
answer correctness
faithfulness / provenance correctness
recall@k
MRR
latency
token cost
drift_visibility_gain
useful_lateral_discovery
over_drift_rate
return_vector_usage
anti_tree_stability
```

Decision rule:

```text
Continue Nollm if gravity reports improve recall judgment or lateral discovery enough to justify complexity.
Reconsider Nollm if drift reports are unused decoration or add no value beyond embedding similarity.
```

---

## Global Non-Goals

Do not build:

```text
new vector DB
full graph database
full agent memory platform
stable public recall API before experiment
multi-chart gluing before gravity V1
automatic persistent writeback from recall
```
