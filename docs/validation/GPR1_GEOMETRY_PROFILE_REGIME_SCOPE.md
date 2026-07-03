# GPR1 Geometry Profile / Parameter-Regime Scope

GPR1 is pure synthetic geometry validation. It calls the sealed DG1 public
geometry schedule, chart, hex, coverage, and metric APIs to summarize a fixed
finite parameter-regime window.

The validation covers A-E from `PARAMETER_MATRIX`, all default phase samples,
both layer phase policies, gaps 1/2/4/8/16, source axial disk radius 0, target
neighborhood radius 4, threshold 1e-9, and DG1 default float64 tolerance. For
each gap, coverage samples every legal base layer `l` in `range(0, 17 - gap)`,
then computes DG1 distributions for each source cell in that layer pair.

With source radius 0, `n = 17 - gap` for each metric row. Gap 16 therefore has
only one distribution and is explicitly a single-pair finite-window
degeneration, not multilayer entropy or nesting evidence.

GPR1 does not select a new production profile, does not change `FIELD_PROFILE_ID`,
does not modify beta, theta, translation, or phase policy, and does not touch
memory, capture, admission, assembly, recall, runtime, OpenClaw, LLM/NLP,
embedding, network, database, or cache paths.
