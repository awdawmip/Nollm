# GRF Migration Boundary

The GRF migration boundary is import-only and explicitly named
`migration_boundary_import_only`.

Supported prototype inputs:

- HCG-like capture JSON envelope
- OCA-like explicit capture input
- minimal V2 DreamShard-like object
- minimal GRF placement/admission fixture

The importer accepts plain dictionaries and maps a stable subset into GRF
objects. It does not import, call, or execute HCG, HAG, HX, OCA, OpenClaw,
terminal runtime, network, database, embedding, or graph/vector search code.

Host request ids, OpenClaw message ids, and adapter request ids remain
provenance refs. They do not become GRF evidence identity unless an input
explicitly provides `shard_id`.
