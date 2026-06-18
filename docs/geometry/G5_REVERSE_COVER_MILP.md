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
