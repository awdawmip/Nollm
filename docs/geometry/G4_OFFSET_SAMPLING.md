# G4 Offset Sampling

G4 is an experimental internal geometry-analysis layer.

It measures how strict true-tiling coverage metrics change when a target layer
is shifted relative to the source layer. Offsets are expressed in target-layer
lattice coordinates `(u, v)` and converted to world translation by the target
layer basis vectors.

G4 reports per-sample coverage count, source-share sum, participation ratio,
entropy, exact containment count, and boundary ambiguity count. It also reports
population-variance aggregates per profile and step.

G4 does not decide recall behavior, change the default profile, reject far
drift, confirm placement, create anchors, create parent-child geometry, or
expand the stable tool surface.

`medium_practical` may be more offset-robust in some metrics. `default_dream`
remains the default because the V4 decision is based on finite-depth multi-step
stability, not offset robustness alone.
