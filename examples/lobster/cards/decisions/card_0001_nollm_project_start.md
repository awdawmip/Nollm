---
id: card_0001_nollm_project_start
type: decision
anchors:
  - project:nollm
  - decision:identity
  - protocol:core
created: 2026-06-12
status: active
ledger_event: evt_0001
---

# Nollm Project Start

Nollm is an external notebook for LLMs, not another LLM or autonomous memory engine.

This decision establishes the Core/Cortex boundary. Nollm Core stores stable, auditable memory records. Nollm Cortex may help an LLM orient, recall, and propose writes, but it does not become the source of truth.

