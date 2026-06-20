# OCP10 Primary Recall-Digest Grounding Report

Status: implementation completed; live acceptance not passed.

OCP10 adds a structured `NOLLM_RECALL_DIGEST` envelope and a generic blind-primary grounding contract. The contract contains no source memory facts, source paths, or fixture facts. The OpenClaw configure helper writes the generic instruction into the blind primary workspace as `AGENTS.md` and configures Active Memory with a short `promptOverride` so the Cortex returns the envelope instead of unstructured prose.

## Implemented

- Active Memory tool surface remains the OCP10 geometry/status surface only.
- Cortex prompt requires `field_state`, `facts`, `explicit_absences`, `lateral_context`, and `scope_note`.
- `facts` are restricted to shards read through `nollm_read`.
- `explicit_absences` must carry requested-but-unread status/progress/blocker/roadmap/next-step categories.
- Stale fields must emit a refresh-required boundary and no facts.
- Primary grounding instructions tell the blind primary to use digest facts only, preserve explicit absences, avoid progress/status extrapolation, avoid source-read claims, and not offer Nollm/source-memory writes.

## Live Finding

G1 did not reach OCP10 acceptance reliably.

One live run produced a valid structured digest with explicit absences for Atlas progress, blockers, next steps, status, and roadmap. The primary did not say Atlas was advancing, but it still suggested future Nollm memory writing, which is outside the allowed response boundary.

A later live run showed a stricter failure: the primary still had Nollm tools visible because OpenClaw Active Memory inherits the target agent tool policy. The primary bypassed the digest path, called Nollm tools directly, and produced unsupported diagnostic claims. When the primary was configured with only `session_status`, Active Memory could no longer run the Nollm tool sequence for that agent.

## Conclusion

`primary_grounding_not_reliable`

The structured envelope and generic grounding instruction are implemented and tested, but current OpenClaw Active Memory coupling prevents simultaneously satisfying both:

- Active Memory can call Nollm tools for the target primary agent.
- The blind primary is unable to call those same Nollm tools.

This is an OpenClaw integration boundary, not a Nollm Core geometry issue. Nollm Core still does not compose prose, select semantic entries, write source memory, use embeddings, use vector search, use graph search, or map `drift_class` to trust/status.

Evidence: `docs/integration/openclaw/evidence/ocp10_primary_recall_digest_grounding_20260621.json`.
