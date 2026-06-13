# Sample Recall Digest

## query_or_task

Recall the starting identity decision for Nollm.

## memory_intent

`recall_focus`

## anchors_used

- `project:nollm`
- `decision:identity`
- `protocol:core`

## cards_read

- `nollm://openclaw/card/card_0001_nollm_project_start`
- `nollm://openclaw/card/card_0002_honeycomb_metadata_alignment`

## active_anchor_fields

- `architecture_is_index`
- `sqlite_audit_projection`

## scale_path

- layer `1`, card `nollm://openclaw/card/card_0002_honeycomb_metadata_alignment`, anchor fields `architecture_is_index`, `sqlite_audit_projection`
- metadata-only; Core did not perform geometry-based recall

## lateral_recovery

- none

## sufficient_scale_reached

true

## recalled_points

- Nollm is an external notebook for LLMs.
- Nollm is not another LLM or autonomous memory engine.
- Core stores stable, auditable memory.
- Cortex orients the LLM but does not become the source of truth.

## warnings

- The sample digest is illustrative and not canonical memory.

## do_not_assume

- Do not assume Nollm includes embeddings, vector search, or autonomous memory mutation.

## source_addresses

- `nollm://openclaw/card/card_0001_nollm_project_start`
- `nollm://openclaw/card/card_0002_honeycomb_metadata_alignment`
- `nollm://openclaw/ledger/event/evt_0001`

## open_questions

- What exact card types should v0.1 standardize?
- How strict should anchor validation be?

## orientation

- `memory_intent`: `recall_surface`
- `candidate_anchors`: `project:nollm`, `decision:identity`, `protocol:core`
- `read_depth`: `surface`

## surfaces_read

- `project:nollm`

## focus_filters

- `limit`: 5
- `include_body`: false

## fallback_mode

`none`

## fallback_reason

none

## fallback_warning

none

## anchors_discovered_from_cards

- none
