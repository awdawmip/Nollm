---
id: card_0002_honeycomb_metadata_alignment
title: Honeycomb Metadata Alignment
type: decision
anchors:
  - project:nollm
  - protocol:core
created: 2026-06-12
status: confirmed
claim: Nollm Core preserves honeycomb, anchor field, and scale link metadata without becoming a geometry runtime.
reason: Align the reference runtime with the P5 architecture while keeping Core deterministic and auditable.
source: human_decision
trust: human-approved
evidence_refs:
  - nollm://openclaw/ledger/event/evt_0002
implications:
  - Anchor is Field, not Folder.
  - Cards exist at a scale.
  - There is no leaf layer.
  - Scale links are not parent-child links.
do_not_infer:
  - Nollm Core computes hex placement.
  - Nollm Core performs polygon overlap calculation.
  - Scale links define a tree.
ledger_event: evt_0002
layer: 1
hex:
  q: 0
  r: 0
  rotation: 22.5
  scale: 0.8408964153
anchor_fields:
  architecture_is_index:
    weight: 0.9
    role: primary
  sqlite_audit_projection:
    weight: 0.5
    role: supporting
scale_links:
  coarser: []
  finer: []
  overlaps: []
  recovery: []
---

# Honeycomb Metadata Alignment

Nollm Core stores the card's layer, hex coordinate metadata, anchor field influence, and scale links as auditable front matter.

Anchor is Field, not Folder. A card exists at a scale, but no scale is an absolute leaf layer. Scale links may help Cortex orient across scale, but they are not parent-child links and do not create a tree.

Core preserves and validates this metadata. Cortex may interpret it during orientation.
