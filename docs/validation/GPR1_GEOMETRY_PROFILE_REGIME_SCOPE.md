# GPR1 Geometry Profile / Parameter-Regime Scope

GPR1 is pure synthetic geometry validation. It calls the sealed DG1 public
geometry schedule, chart, hex, coverage, and metric APIs to summarize a fixed
finite parameter-regime window.

The validation covers A-E from `PARAMETER_MATRIX`, all default phase samples,
both layer phase policies, gaps 1/2/4/8/16, source axial disk radius 0, target
neighborhood radius 4, threshold 1e-9, and DG1 default float64 tolerance.

GPR1 does not select a new production profile, does not change `FIELD_PROFILE_ID`,
does not modify beta, theta, translation, or phase policy, and does not touch
memory, capture, admission, assembly, recall, runtime, OpenClaw, LLM/NLP,
embedding, network, database, or cache paths.
