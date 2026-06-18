# G3 Multi-Step Coverage Metrics

G3 is an experimental internal geometry-analysis layer.

It measures finite-depth coverage behavior for canonical parameter profiles by
projecting a layer-0 source cell to target layers `n = 1..8` with the strict
true-tiling Model T kernel.

The metrics include coverage count, source-share sum, participation ratio,
entropy, exact containment count, and boundary ambiguity count. `source_share`
is used for contribution accounting. `target_share` is used for exact
containment.

G3 does not decide recall, impose drift limits, create parent/child hierarchy,
confirm placement, write cards, create anchors, or expand the stable tool
surface.

Later G4/G5/G7/G8 experiments may consume G3 reports by `profile_id`, but those
experiments remain separate tasks.
