# DR1 Recall Resolver Scope

DR1 is the first read-only Recall layer for Dream Geometry V2.

It consumes supplied DC1 Query Probe objects, explicit finite RecallUniverse
objects, read-only DE1 evidence, DG1 directed coverage outputs, and DG2 Field
objects. It produces an ephemeral RecallDigest.

DR1 does not add runtime integration, CLI commands, OpenClaw paths, adapter
behavior, persistence, SQLite, embeddings, vector search, NLP extraction,
geometry recall, automatic card placement, automatic anchors, or automatic
context composition.

The implemented foundation covers:

- exact query atom projection;
- caller-supplied relative-time resolution deferral, strict span binding, and rejection of fabricated spans;
- strict finite RecallUniverse validation, including current proposal receipts and cover policy identity;
- stable cover seeding from accepted trace support;
- executed finite `K_up` / `K_down` traversal with residual diagnostics;
- budget exhaustion outcomes and structured traversal discards;
- DreamShard usage-state qualification with primary/context evidence partitions;
- interpretation and revision context identifiers;
- internal gravity tie-break metadata only for equal-core-score candidates;
- legacy DC1 read-only context exclusion from seeding.

DR1.1 closes DR1. DR1 is sealed after this closure; further DR1.x hardening is
not authorized without a new task pack.
