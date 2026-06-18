# G7 Mode 3 Free-Drift Trace Experiment

G7 is an internal experiment, not a stable recall product or public tool
surface.

Candidates come from an external retrieval layer. Nollm does not compute the
retrieval score and does not reject candidates because they are far from the
entry Gravity Well. It adds Gravity Reports and deterministic visibility labels
so an LLM-facing digest can see `R`, `S`, `A`, `drift_class`, and
`projection_method` for each candidate.

Mode 3 free drift means far lateral candidates and semantic breaks remain
visible in the trace. The labels are instrumentation, not permissions or
filters.

The experiment does not write cards, create anchors, persist recall results as
memory, or map drift classes to trust/status. It is preparation for ablation,
not proof that gravity reports improve recall.
