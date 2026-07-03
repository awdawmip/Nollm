# GPR1 Geometry Profile / Parameter-Regime Validation

GPR1 records finite, reproducible geometry diagnostics for the existing DG1
parameter matrix. It is a research validation stage, not a production profile
selection mechanism.

## Contract

- Inputs are limited to sealed DG1 public geometry objects and the existing A-E
  parameter matrix, default phase samples, and layer phase policies.
- Coverage distributions are produced by DG1 `compute_distribution`; GPR1 does
  not implement polygon overlap or coverage kernels.
- Metrics are finite-window diagnostics for branching, effective count,
  residual mass, quantized overlap entropy, nesting tendency, phase recurrence,
  and rotation recurrence modulo 60 degrees.
- B is reported as the current engineering baseline: `beta = 2^(1/4)`,
  density growth `beta^2 = sqrt(2)`, and delta theta `22.5` degrees.

## Limits

- Finite-window metrics are not all-plane global proofs.
- Float64 tolerance is not exact algebraic-number proof.
- Phase policies remain diagnostic and are not global translation policy.
- No admission, field, recall, runtime, OpenClaw, LLM/NLP, embedding, semantic
  search, network, database, or cache behavior is exercised.
