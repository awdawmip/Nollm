# GRF Query Generalization

GRF prototype recall supports these public entry modes:

- explicit_cell
- shard_id
- island_id
- patch_id
- source_window
- admission_id
- placement_id

`GRFFacade` resolves file-backed identifiers with exact GRFFileStore lookups
before recall. No lexical, vector, embedding, or global search fallback is
allowed.
