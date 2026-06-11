---
id: card_0001_nollm_project_start
title: Nollm Project Start
type: decision
anchors:
  - project:nollm
  - decision:identity
  - protocol:core
created: 2026-06-12
status: confirmed
claim: Nollm is an external notebook for LLMs, not another LLM or autonomous memory engine.
reason: Establish the project identity and Core/Cortex boundary.
source: human_decision
trust: human-approved
evidence_refs:
  - nollm://lobster/ledger/event/evt_0001
implications:
  - Keep Core deterministic and auditable.
  - Keep Cortex model-side and advisory.
do_not_infer:
  - Nollm provides model inference.
  - Nollm autonomously mutates memory.
ledger_event: evt_0001
---

# Nollm Project Start

Nollm is an external notebook for LLMs, not another LLM or autonomous memory engine.

This decision establishes the Core/Cortex boundary. Nollm Core stores stable, auditable memory records. Nollm Cortex may help an LLM orient, recall, and propose writes, but it does not become the source of truth.

## Do Not Infer

- Nollm provides model inference.
- Nollm autonomously mutates memory.
