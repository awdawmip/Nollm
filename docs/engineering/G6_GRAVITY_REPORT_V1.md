# G6 Gravity Report V1

G6 is an internal experimental helper for computing Gravity Report V1 records.

V1 implements only `R_column_ring`, `S_scale_delta`,
`A_anchor_similarity`, `drift_class`, and `projection_method`. Anchor
similarity uses nonnegative cosine over anchor vectors and is written as a
clamped `[0, 1]` value.

Gravity is instrumentation, not restriction. The report labels drift from an
entry Gravity Well to a content Gravity Mark; it does not decide recall,
reject content, create cards, create anchors, write memory, or change
trust/status.

Free drift recall and later G7 experiments remain outside this implementation
and are not stable recall/tool surface.
