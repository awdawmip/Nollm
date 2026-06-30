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
- caller-supplied relative-time resolution deferral and inclusion;
- stable cover seeding from accepted trace support;
- directed coverage residual diagnostics;
- DreamShard usage-state qualification;
- interpretation and revision context identifiers;
- internal gravity tie-break metadata;
- legacy DC1 read-only context exclusion from seeding.
