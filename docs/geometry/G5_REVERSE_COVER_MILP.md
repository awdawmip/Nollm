# G5 Reverse-Cover MILP

G5 is an experimental internal geometry-analysis layer.

It measures reverse-cover behavior for strict true-tiling Model T profiles by
building a finite target-layer hex cluster, a deterministic layer-0 source
candidate window, and a binary incidence matrix where positive polygon overlap
means coverage.

The report compares a deterministic greedy feasible cover, SciPy/HiGHS MILP
when available, an LP lower bound when available, and simple deterministic
lower-bound diagnostics. A MILP result is called optimal only when the solver
status is `OPTIMAL`; limited or unavailable solver results are never reported
as `opt`, and gap metrics are emitted only for proven optima.

G5 does not decide recall behavior, write cards, create anchors, confirm
placement, create parent-child geometry, change trust/status, or expand the
stable tool surface.

## G5b Nontrivial Cluster Pack

The smoke cases are centered radius-1 clusters. They are useful for checking
solver plumbing, but they are too shallow for engineering comparison.

G5b adds deterministic nontrivial cases: centered radius sweeps and fixed
boundary-offset clusters. These cases are an engineering pack, not a theorem
about every possible cluster. They report pack summaries and A/B comparison
metrics only from measured values.

Timeout or limited MILP results remain incumbents, not optima. Benchmark ease
or nontrivial-pack behavior is not a reason to change the default geometry.
