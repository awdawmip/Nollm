# Source

Source records where a card claim came from. It helps Cortex separate remembered material from inference.

## Source Kinds

- `user_statement`: A direct user statement.
- `human_decision`: An explicit human decision.
- `project_file`: A source-of-truth project file.
- `ledger_event`: A ledgered Core event.
- `external_reference`: A cited source outside the notebook.
- `llm_inference`: A model-side inference or synthesis.

## Rule

LLM inference must not be recorded as a confirmed stable notebook record without operator approval and a source change or supporting source. It may be written as `draft`, `candidate`, `hypothesis`, or another clearly tentative form.

## MT1 Source Identity

MT1 archive ingest separates blob identity, source-entry identity, span identity, and source references. Blob identity is a content hash and may be shared by equal bytes. Source-entry identity is unique per snapshot source path. Span identity is source-entry identity plus byte range/ordinal. Source references bind snapshot id, source object id, blob hash, and byte range.

Trust and state metadata (`origin_kind`, `operational_state`, `epistemic_state`, `source_policy_id`) must be preserved from the archive source entry into imported shards.
