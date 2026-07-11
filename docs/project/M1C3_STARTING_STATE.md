# M1C3 Starting State

```text
input bundle = nollm_m1c2_complete_kernel_canonical_evidence_serialized_transaction_20260711_6715cdb7.bundle
input SHA-256 = 0aeb24737fc6ae031b876b4b74f573d2ac65e1c1e2ea2172db4ff33aafd13cb6
input HEAD = 6715cdb7edbac63907805079ef1cbbc973dd2887
input worktree = clean
M1C2 packages = Core 21, Snapshot 4, Trace 1, Access 27
M0 = 18; architecture/hygiene = 8; GRF = 112
production violations = 0; production cycles = 0
```

Preserved blockers: mixed None/string phase sorting fails; registry template
metadata and fanout are mutable; contradictory direct CoverageTemplate values
are accepted; unsorted Anchor cells are accepted; custom fanout repeats ring 1
for ring 2; distinct CoreRuntime owners can stale-overwrite one workspace; and
Access Recall can observe a Core/Binding transaction midstate.
