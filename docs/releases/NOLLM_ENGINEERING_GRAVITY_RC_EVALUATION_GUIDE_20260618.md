# Nollm Engineering Gravity RC Evaluation Guide

Date: 2026-06-18

This guide is for external evaluation of the G-series engineering gravity
scaffold. It is not a product recall API and not proof of long-term memory.

## What To Test

- Whether gravity reports reduce misuse of far-drift content.
- Whether lateral discoveries become visible.
- Whether return vectors help re-center.
- Whether the B profile is more stable in finite-depth scale scan.
- Whether the A profile is more robust under offset noise.

## Ablation Conditions

```text
N0: Vector RAG only
N1: Vector RAG + geometry mark only
N2: Vector RAG + gravity report
N3: Vector RAG + gravity report + return vector
N4: medium_practical profile, sqrt(2) / 15 deg
N5: default_dream profile, 2^(1/4) / 22.5 deg
```

## Success Criteria

- Gravity reports improve judgment.
- Over-drift is more visible.
- Useful lateral discovery is visible.
- Return vector improves re-centering.
- B/A profile differences remain measurable.

## Failure Criteria

- Gravity reports are unused decoration.
- Geometry mark adds no value beyond embedding similarity.
- Free drift mainly increases hallucination risk.
- Implementation cost exceeds measurable benefit.

## Warnings

```text
Do not treat the RC scaffold as a product recall API.
Do not use drift_class as trust/status.
Do not auto-write drifted recall into persistent memory.
```

The evaluator should judge whether the scaffold improves model-side recall
judgment, not whether it replaces retrieval, validation, operator approval, or
Nollm Core's deterministic filesystem protocol.
