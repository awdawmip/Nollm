# NOLLM GRF7 Final Architecture Report

GRF7 adds a metadata-only global directory over replaceable local GRF
partitions. Core retains the inward dependency direction: global field code
imports local deterministic GRF services but no Adapter, Host runtime, or
Terminal package. Adapters parse the versioned Host Contract and call Core;
Hosts do not mutate field state directly.

Global query routing is typed and explicit. Local recall remains the existing
`RelationField`; global propagation follows only recorded, confidence-checked
bridges under hop, fanout, activation, and result budgets. Partition snapshots
and ledgers support deterministic replacement and replay.

Evidence remains the fact source. Geometry, directory placement, recall paths,
and stitches are auditable relation machinery, not proof or fact merge. The
runtime adds no float geometry, polygon computation, embedding main index,
semantic graph main path, or Terminal memory store.

`GATE_J_PASS`.
